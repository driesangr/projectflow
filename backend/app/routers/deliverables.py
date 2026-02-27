"""CRUD router for Deliverables."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import check_artifact_permission
from app.database import get_db
from app.models.audit_log import AuditAction, AuditLog
from app.models.deliverable import Deliverable
from app.models.role_permission import ArtifactType
from app.models.topic import Topic
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.deliverable import DeliverableCreate, DeliverableMove, DeliverableResponse, DeliverableUpdate
from app.schemas.reorder import ReorderItem
from app.services.maturity import recalculate_upwards

router = APIRouter(prefix="/deliverables", tags=["deliverables"])


async def _deliverable_project_id(d: Deliverable, db: AsyncSession) -> UUID:
    """Resolve the project_id for a deliverable (via topic if needed)."""
    if d.project_id:
        return d.project_id
    topic = await db.get(Topic, d.topic_id)
    return topic.project_id


@router.get("/", response_model=list[DeliverableResponse], summary="List deliverables")
async def list_deliverables(
    topic_id: UUID | None = Query(default=None),
    project_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Deliverable]:
    query = select(Deliverable).where(Deliverable.is_deleted.is_(False))
    if topic_id:
        query = query.where(Deliverable.topic_id == topic_id)
    if project_id:
        query = query.where(Deliverable.project_id == project_id)
    result = await db.execute(query.order_by(Deliverable.position.asc(), Deliverable.created_at.asc()))
    return result.scalars().all()


@router.patch("/reorder", status_code=status.HTTP_204_NO_CONTENT, summary="Reorder deliverables")
async def reorder_deliverables(
    items: list[ReorderItem],
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    for item in items:
        deliverable = await db.get(Deliverable, item.id)
        if deliverable and not deliverable.is_deleted:
            deliverable.position = item.position
    await db.commit()


@router.get(
    "/{deliverable_id}", response_model=DeliverableResponse,
    summary="Get deliverable by ID"
)
async def get_deliverable(
    deliverable_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Deliverable:
    deliverable = await db.get(Deliverable, deliverable_id)
    if not deliverable or deliverable.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deliverable not found")
    pid = await _deliverable_project_id(deliverable, db)
    if not await check_artifact_permission(current_user, pid, ArtifactType.deliverable, "read", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied: 'read' on 'deliverable'.")
    return deliverable


@router.post(
    "/", response_model=DeliverableResponse, status_code=status.HTTP_201_CREATED,
    summary="Create a deliverable"
)
async def create_deliverable(
    payload: DeliverableCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Deliverable:
    if payload.topic_id:
        topic = await db.get(Topic, payload.topic_id)
        pid = topic.project_id if topic else payload.project_id
        count_filter = Deliverable.topic_id == payload.topic_id
    else:
        pid = payload.project_id
        count_filter = Deliverable.project_id == payload.project_id
    if not await check_artifact_permission(current_user, pid, ArtifactType.deliverable, "create", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied: 'create' on 'deliverable'.")
    count_res = await db.execute(
        select(func.count(Deliverable.id)).where(
            count_filter,
            Deliverable.is_deleted.is_(False),
        )
    )
    deliverable = Deliverable(**payload.model_dump())
    deliverable.position = count_res.scalar() or 0
    db.add(deliverable)
    await db.flush()

    db.add(AuditLog(
        entity_type="Deliverable",
        entity_id=deliverable.id,
        action=AuditAction.created,
        changed_by=current_user.username,
        changed_at=datetime.now(timezone.utc),
        changes={"title": deliverable.title},
    ))
    await db.commit()
    await db.refresh(deliverable)
    return deliverable


@router.put(
    "/{deliverable_id}", response_model=DeliverableResponse,
    summary="Update a deliverable"
)
async def update_deliverable(
    deliverable_id: UUID,
    payload: DeliverableUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Deliverable:
    deliverable = await db.get(Deliverable, deliverable_id)
    if not deliverable or deliverable.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deliverable not found")
    pid = await _deliverable_project_id(deliverable, db)
    if not await check_artifact_permission(current_user, pid, ArtifactType.deliverable, "write", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied: 'write' on 'deliverable'.")

    changes: dict = {}
    status_changed = False
    for field, value in payload.model_dump(exclude_unset=True).items():
        old = getattr(deliverable, field)
        if old != value:
            changes[field] = {"old": str(old), "new": str(value)}
            setattr(deliverable, field, value)
            if field == "status":
                status_changed = True

    if changes:
        db.add(AuditLog(
            entity_type="Deliverable",
            entity_id=deliverable.id,
            action=AuditAction.updated,
            changed_by=current_user.username,
            changed_at=datetime.now(timezone.utc),
            changes=changes,
        ))

    if status_changed and deliverable.topic_id:
        from app.services.maturity import calculate_topic_maturity
        await calculate_topic_maturity(deliverable.topic_id, db)

    await db.commit()
    await db.refresh(deliverable)
    return deliverable


@router.post(
    "/{deliverable_id}/duplicate", response_model=DeliverableResponse,
    status_code=status.HTTP_201_CREATED, summary="Duplicate a deliverable"
)
async def duplicate_deliverable(
    deliverable_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Deliverable:
    source = await db.get(Deliverable, deliverable_id)
    if not source or source.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deliverable not found")
    pid = await _deliverable_project_id(source, db)
    if not await check_artifact_permission(current_user, pid, ArtifactType.deliverable, "create", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied: 'create' on 'deliverable'.")

    # Determine parent filter for sibling queries
    if source.topic_id:
        parent_filter = Deliverable.topic_id == source.topic_id
    else:
        parent_filter = Deliverable.project_id == source.project_id

    # Fetch existing titles in the same parent to guarantee uniqueness
    titles_result = await db.execute(
        select(Deliverable.title).where(
            parent_filter,
            Deliverable.is_deleted.is_(False),
        )
    )
    existing_titles = {row[0] for row in titles_result.fetchall()}

    # Generate "title Kopie_1", "title Kopie_2", … until unique
    counter = 1
    while True:
        candidate = f"{source.title} Kopie_{counter}"
        if candidate not in existing_titles:
            break
        counter += 1

    count_res = await db.execute(
        select(func.count(Deliverable.id)).where(
            parent_filter,
            Deliverable.is_deleted.is_(False),
        )
    )
    copy = Deliverable(
        title=candidate,
        description=source.description,
        epic_points=source.epic_points,
        business_value=source.business_value,
        status=source.status,
        owner_name=source.owner_name,
        topic_id=source.topic_id,
        project_id=source.project_id,
        position=count_res.scalar() or 0,
    )
    db.add(copy)
    await db.flush()

    db.add(AuditLog(
        entity_type="Deliverable",
        entity_id=copy.id,
        action=AuditAction.created,
        changed_by=current_user.username,
        changed_at=datetime.now(timezone.utc),
        changes={"title": copy.title, "duplicated_from": str(deliverable_id)},
    ))
    await db.commit()
    await db.refresh(copy)
    return copy


@router.patch(
    "/{deliverable_id}/move", response_model=DeliverableResponse,
    summary="Move a deliverable to a different parent"
)
async def move_deliverable(
    deliverable_id: UUID,
    payload: DeliverableMove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Deliverable:
    deliverable = await db.get(Deliverable, deliverable_id)
    if not deliverable or deliverable.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deliverable not found")
    pid = await _deliverable_project_id(deliverable, db)
    if not await check_artifact_permission(current_user, pid, ArtifactType.deliverable, "write", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied: 'write' on 'deliverable'.")

    old_topic_id = deliverable.topic_id

    deliverable.topic_id = payload.topic_id
    deliverable.project_id = payload.project_id

    db.add(AuditLog(
        entity_type="Deliverable",
        entity_id=deliverable.id,
        action=AuditAction.updated,
        changed_by=current_user.username,
        changed_at=datetime.now(timezone.utc),
        changes={
            "topic_id": {"old": str(old_topic_id), "new": str(payload.topic_id)},
            "project_id": {"old": str(deliverable.project_id), "new": str(payload.project_id)},
        },
    ))

    await db.commit()
    await db.refresh(deliverable)

    # Recalculate maturity for old topic
    if old_topic_id:
        from app.services.maturity import calculate_topic_maturity
        await calculate_topic_maturity(old_topic_id, db)
        await db.commit()

    # Recalculate maturity for new topic
    if payload.topic_id:
        from app.services.maturity import calculate_topic_maturity
        await calculate_topic_maturity(payload.topic_id, db)
        await db.commit()

    return deliverable


@router.delete(
    "/{deliverable_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a deliverable"
)
async def delete_deliverable(
    deliverable_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    deliverable = await db.get(Deliverable, deliverable_id)
    if not deliverable or deliverable.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deliverable not found")
    pid = await _deliverable_project_id(deliverable, db)
    if not await check_artifact_permission(current_user, pid, ArtifactType.deliverable, "delete", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied: 'delete' on 'deliverable'.")

    deliverable.is_deleted = True
    deliverable.deleted_at = datetime.now(timezone.utc)

    db.add(AuditLog(
        entity_type="Deliverable",
        entity_id=deliverable.id,
        action=AuditAction.deleted,
        changed_by=current_user.username,
        changed_at=datetime.now(timezone.utc),
        changes={"title": deliverable.title},
    ))
    if deliverable.topic_id:
        from app.services.maturity import calculate_topic_maturity
        await calculate_topic_maturity(deliverable.topic_id, db)
    await db.commit()
