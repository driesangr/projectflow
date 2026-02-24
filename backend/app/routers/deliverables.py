"""CRUD router for Deliverables."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit_log import AuditAction, AuditLog
from app.models.deliverable import Deliverable
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.deliverable import DeliverableCreate, DeliverableResponse, DeliverableUpdate
from app.schemas.reorder import ReorderItem
from app.services.maturity import recalculate_upwards

router = APIRouter(prefix="/deliverables", tags=["deliverables"])


@router.get("/", response_model=list[DeliverableResponse], summary="List deliverables")
async def list_deliverables(
    topic_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Deliverable]:
    query = select(Deliverable).where(Deliverable.is_deleted.is_(False))
    if topic_id:
        query = query.where(Deliverable.topic_id == topic_id)
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
    _: User = Depends(get_current_user),
) -> Deliverable:
    deliverable = await db.get(Deliverable, deliverable_id)
    if not deliverable or deliverable.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deliverable not found")
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
    count_res = await db.execute(
        select(func.count(Deliverable.id)).where(
            Deliverable.topic_id == payload.topic_id,
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

    if status_changed:
        from app.services.maturity import calculate_topic_maturity
        await calculate_topic_maturity(deliverable.topic_id, db)

    await db.commit()
    await db.refresh(deliverable)
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
    from app.services.maturity import calculate_topic_maturity
    await calculate_topic_maturity(deliverable.topic_id, db)
    await db.commit()
