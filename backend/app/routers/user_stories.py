"""CRUD router for UserStories."""

import re
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit_log import AuditAction, AuditLog
from app.models.deliverable import Deliverable
from app.models.task import Task
from app.models.topic import Topic
from app.models.user import User
from app.models.user_story import UserStory
from app.routers.auth import get_current_user
from app.schemas.reorder import ReorderItem
from app.schemas.user_story import (
    UserStoryCreate, UserStoryResponse, UserStoryUpdate,
    UserStoryDuplicateRequest, StoryValueItem,
)
from app.services.maturity import recalculate_upwards

router = APIRouter(prefix="/user-stories", tags=["user_stories"])


@router.get("/", response_model=list[UserStoryResponse], summary="List user stories")
async def list_user_stories(
    deliverable_id: UUID | None = Query(default=None),
    sprint_id: UUID | None = Query(default=None),
    project_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[UserStory]:
    query = select(UserStory).where(UserStory.is_deleted.is_(False))
    if deliverable_id:
        query = query.where(UserStory.deliverable_id == deliverable_id)
    if sprint_id:
        query = query.where(UserStory.sprint_id == sprint_id)
    if project_id:
        query = (
            query
            .join(Deliverable, UserStory.deliverable_id == Deliverable.id)
            .join(Topic, Deliverable.topic_id == Topic.id)
            .where(Topic.project_id == project_id)
            .where(Deliverable.is_deleted.is_(False))
            .where(Topic.is_deleted.is_(False))
        )
    result = await db.execute(query.order_by(UserStory.position.asc(), UserStory.created_at.asc()))
    return result.scalars().all()


@router.patch("/reorder", status_code=status.HTTP_204_NO_CONTENT, summary="Reorder user stories")
async def reorder_user_stories(
    items: list[ReorderItem],
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    for item in items:
        story = await db.get(UserStory, item.id)
        if story and not story.is_deleted:
            story.position = item.position
    await db.commit()


@router.patch("/bulk-values", status_code=status.HTTP_204_NO_CONTENT, summary="Bulk update story values")
async def bulk_update_story_values(
    items: list[StoryValueItem],
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    for item in items:
        story = await db.get(UserStory, item.id)
        if story and not story.is_deleted:
            if item.business_value is not None:
                story.business_value = item.business_value
            if item.sprint_value is not None:
                story.sprint_value = item.sprint_value
    await db.commit()


@router.post(
    "/{story_id}/duplicate", response_model=UserStoryResponse,
    status_code=status.HTTP_201_CREATED, summary="Duplicate a user story"
)
async def duplicate_user_story(
    story_id: UUID,
    payload: UserStoryDuplicateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserStory:
    source = await db.get(UserStory, story_id)
    if not source or source.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User story not found")

    # Find unique title within same deliverable
    titles_res = await db.execute(
        select(UserStory.title).where(
            UserStory.deliverable_id == source.deliverable_id,
            UserStory.is_deleted.is_(False),
        )
    )
    existing_titles = {row[0] for row in titles_res.fetchall()}
    base_title = re.sub(r'_Kopie_\d+$', '', source.title)
    counter = 1
    while True:
        candidate = f"{base_title}_Kopie_{counter}"
        if candidate not in existing_titles:
            break
        counter += 1

    count_res = await db.execute(
        select(func.count(UserStory.id)).where(
            UserStory.deliverable_id == source.deliverable_id,
            UserStory.is_deleted.is_(False),
        )
    )

    copy = UserStory(
        title=candidate,
        description=source.description,
        acceptance_criteria=source.acceptance_criteria,
        story_points=source.story_points,
        business_value=source.business_value,
        sprint_value=source.sprint_value,
        status="todo",
        owner_name=source.owner_name,
        deliverable_id=source.deliverable_id,
        sprint_id=source.sprint_id,
        position=count_res.scalar() or 0,
    )
    db.add(copy)
    await db.flush()

    # Copy selected tasks in original order
    if payload.task_ids:
        task_id_set = set(payload.task_ids)
        tasks_res = await db.execute(
            select(Task)
            .where(Task.user_story_id == source.id, Task.is_deleted.is_(False))
            .order_by(Task.position.asc())
        )
        source_tasks = tasks_res.scalars().all()
        pos = 0
        for t in source_tasks:
            if t.id in task_id_set:
                db.add(Task(
                    title=t.title,
                    description=t.description,
                    status=t.status,
                    effort_hours=t.effort_hours,
                    sprint_value=t.sprint_value,
                    owner_name=t.owner_name,
                    user_story_id=copy.id,
                    position=pos,
                ))
                pos += 1

    db.add(AuditLog(
        entity_type="UserStory",
        entity_id=copy.id,
        action=AuditAction.created,
        changed_by=current_user.username,
        changed_at=datetime.now(timezone.utc),
        changes={"title": copy.title, "duplicated_from": str(source.id)},
    ))
    await db.commit()
    await db.refresh(copy)
    return copy


@router.get(
    "/{story_id}", response_model=UserStoryResponse,
    summary="Get user story by ID"
)
async def get_user_story(
    story_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> UserStory:
    story = await db.get(UserStory, story_id)
    if not story or story.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User story not found")
    return story


@router.post(
    "/", response_model=UserStoryResponse, status_code=status.HTTP_201_CREATED,
    summary="Create a user story"
)
async def create_user_story(
    payload: UserStoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserStory:
    count_res = await db.execute(
        select(func.count(UserStory.id)).where(
            UserStory.deliverable_id == payload.deliverable_id,
            UserStory.is_deleted.is_(False),
        )
    )
    story = UserStory(**payload.model_dump())
    story.position = count_res.scalar() or 0
    db.add(story)
    await db.flush()

    db.add(AuditLog(
        entity_type="UserStory",
        entity_id=story.id,
        action=AuditAction.created,
        changed_by=current_user.username,
        changed_at=datetime.now(timezone.utc),
        changes={"title": story.title},
    ))

    await recalculate_upwards("user_story", story.id, db)
    await db.commit()
    await db.refresh(story)
    return story


@router.put(
    "/{story_id}", response_model=UserStoryResponse,
    summary="Update a user story"
)
async def update_user_story(
    story_id: UUID,
    payload: UserStoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserStory:
    story = await db.get(UserStory, story_id)
    if not story or story.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User story not found")

    changes: dict = {}
    status_changed = False
    for field, value in payload.model_dump(exclude_unset=True).items():
        old = getattr(story, field)
        if old != value:
            changes[field] = {"old": str(old), "new": str(value)}
            setattr(story, field, value)
            if field == "status":
                status_changed = True

    if changes:
        db.add(AuditLog(
            entity_type="UserStory",
            entity_id=story.id,
            action=AuditAction.updated,
            changed_by=current_user.username,
            changed_at=datetime.now(timezone.utc),
            changes=changes,
        ))

    if status_changed:
        await recalculate_upwards("user_story", story.id, db)

    await db.commit()
    await db.refresh(story)
    return story


@router.delete(
    "/{story_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a user story"
)
async def delete_user_story(
    story_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    story = await db.get(UserStory, story_id)
    if not story or story.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User story not found")

    story.is_deleted = True
    story.deleted_at = datetime.now(timezone.utc)

    db.add(AuditLog(
        entity_type="UserStory",
        entity_id=story.id,
        action=AuditAction.deleted,
        changed_by=current_user.username,
        changed_at=datetime.now(timezone.utc),
        changes={"title": story.title},
    ))
    await recalculate_upwards("user_story", story.id, db)
    await db.commit()
