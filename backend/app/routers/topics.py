"""CRUD router for Topics."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import check_artifact_permission
from app.database import get_db
from app.models.audit_log import AuditAction, AuditLog
from app.models.project_membership import ProjectMembership
from app.models.role_permission import ArtifactType
from app.models.topic import Topic
from app.models.user import GlobalRole, User
from app.routers.auth import get_current_user
from app.schemas.reorder import ReorderItem
from app.schemas.topic import TopicCreate, TopicResponse, TopicUpdate

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("/", response_model=list[TopicResponse], summary="List topics")
async def list_topics(
    project_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Topic]:
    query = select(Topic).where(Topic.is_deleted.is_(False))

    if project_id:
        # Explicit project filter: verify the caller may read that project
        if not await check_artifact_permission(
            current_user, project_id, ArtifactType.topic, "read", db
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: 'read' on 'topic'.",
            )
        query = query.where(Topic.project_id == project_id)
    elif current_user.global_role not in (GlobalRole.superuser, GlobalRole.admin):
        # No filter given: restrict to topics in projects the user is a member of
        from sqlalchemy import exists
        query = query.where(
            exists().where(
                ProjectMembership.project_id == Topic.project_id,
                ProjectMembership.user_id == current_user.id,
            )
        )

    result = await db.execute(query.order_by(Topic.position.asc(), Topic.created_at.asc()))
    return result.scalars().all()


@router.patch("/reorder", status_code=status.HTTP_204_NO_CONTENT, summary="Reorder topics")
async def reorder_topics(
    items: list[ReorderItem],
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    for item in items:
        topic = await db.get(Topic, item.id)
        if topic and not topic.is_deleted:
            topic.position = item.position
    await db.commit()


@router.get("/{topic_id}", response_model=TopicResponse, summary="Get topic by ID")
async def get_topic(
    topic_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Topic:
    topic = await db.get(Topic, topic_id)
    if not topic or topic.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    if not await check_artifact_permission(current_user, topic.project_id, ArtifactType.topic, "read", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied: 'read' on 'topic'.")
    return topic


@router.post(
    "/", response_model=TopicResponse, status_code=status.HTTP_201_CREATED,
    summary="Create a topic"
)
async def create_topic(
    payload: TopicCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Topic:
    if not await check_artifact_permission(current_user, payload.project_id, ArtifactType.topic, "create", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied: 'create' on 'topic'.")
    # Assign position after existing siblings
    count_res = await db.execute(
        select(func.count(Topic.id)).where(
            Topic.project_id == payload.project_id,
            Topic.is_deleted.is_(False),
        )
    )
    topic = Topic(**payload.model_dump())
    topic.position = count_res.scalar() or 0
    db.add(topic)
    await db.flush()

    db.add(AuditLog(
        entity_type="Topic",
        entity_id=topic.id,
        action=AuditAction.created,
        changed_by=current_user.username,
        changed_at=datetime.now(timezone.utc),
        changes={"title": topic.title},
    ))
    await db.commit()
    await db.refresh(topic)
    return topic


@router.put("/{topic_id}", response_model=TopicResponse, summary="Update a topic")
async def update_topic(
    topic_id: UUID,
    payload: TopicUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Topic:
    topic = await db.get(Topic, topic_id)
    if not topic or topic.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    if not await check_artifact_permission(current_user, topic.project_id, ArtifactType.topic, "write", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied: 'write' on 'topic'.")

    changes: dict = {}
    for field, value in payload.model_dump(exclude_unset=True).items():
        old = getattr(topic, field)
        if old != value:
            changes[field] = {"old": str(old), "new": str(value)}
            setattr(topic, field, value)

    if changes:
        db.add(AuditLog(
            entity_type="Topic",
            entity_id=topic.id,
            action=AuditAction.updated,
            changed_by=current_user.username,
            changed_at=datetime.now(timezone.utc),
            changes=changes,
        ))

    await db.commit()
    await db.refresh(topic)
    return topic


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Soft-delete a topic")
async def delete_topic(
    topic_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    topic = await db.get(Topic, topic_id)
    if not topic or topic.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    if not await check_artifact_permission(current_user, topic.project_id, ArtifactType.topic, "delete", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied: 'delete' on 'topic'.")

    topic.is_deleted = True
    topic.deleted_at = datetime.now(timezone.utc)

    db.add(AuditLog(
        entity_type="Topic",
        entity_id=topic.id,
        action=AuditAction.deleted,
        changed_by=current_user.username,
        changed_at=datetime.now(timezone.utc),
        changes={"title": topic.title},
    ))
    await db.commit()
