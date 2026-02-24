"""CRUD router for Topics."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit_log import AuditAction, AuditLog
from app.models.topic import Topic
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.topic import TopicCreate, TopicResponse, TopicUpdate

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("/", response_model=list[TopicResponse], summary="List topics")
async def list_topics(
    project_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Topic]:
    query = select(Topic).where(Topic.is_deleted.is_(False))
    if project_id:
        query = query.where(Topic.project_id == project_id)
    result = await db.execute(query.order_by(Topic.business_value.desc().nulls_last()))
    return result.scalars().all()


@router.get("/{topic_id}", response_model=TopicResponse, summary="Get topic by ID")
async def get_topic(
    topic_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Topic:
    topic = await db.get(Topic, topic_id)
    if not topic or topic.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
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
    topic = Topic(**payload.model_dump())
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
