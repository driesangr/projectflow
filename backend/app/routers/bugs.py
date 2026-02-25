"""CRUD router for Bugs."""

import re
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit_log import AuditAction, AuditLog
from app.models.bug import Bug
from app.models.deliverable import Deliverable
from app.models.task import Task
from app.models.topic import Topic
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.reorder import ReorderItem
from app.schemas.bug import (
    BugCreate, BugResponse, BugUpdate,
    BugDuplicateRequest, BugValueItem,
)
from app.services.maturity import recalculate_upwards

router = APIRouter(prefix="/bugs", tags=["bugs"])


@router.get("/", response_model=list[BugResponse], summary="List bugs")
async def list_bugs(
    deliverable_id: UUID | None = Query(default=None),
    sprint_id: UUID | None = Query(default=None),
    project_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Bug]:
    query = select(Bug).where(Bug.is_deleted.is_(False))
    if deliverable_id:
        query = query.where(Bug.deliverable_id == deliverable_id)
    if sprint_id:
        query = query.where(Bug.sprint_id == sprint_id)
    if project_id:
        query = (
            query
            .join(Deliverable, Bug.deliverable_id == Deliverable.id)
            .join(Topic, Deliverable.topic_id == Topic.id)
            .where(Topic.project_id == project_id)
            .where(Deliverable.is_deleted.is_(False))
            .where(Topic.is_deleted.is_(False))
        )
    result = await db.execute(query.order_by(Bug.position.asc(), Bug.created_at.asc()))
    return result.scalars().all()


@router.patch("/reorder", status_code=status.HTTP_204_NO_CONTENT, summary="Reorder bugs")
async def reorder_bugs(
    items: list[ReorderItem],
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    for item in items:
        bug = await db.get(Bug, item.id)
        if bug and not bug.is_deleted:
            bug.position = item.position
    await db.commit()


@router.patch("/bulk-values", status_code=status.HTTP_204_NO_CONTENT, summary="Bulk update bug values")
async def bulk_update_bug_values(
    items: list[BugValueItem],
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    for item in items:
        bug = await db.get(Bug, item.id)
        if bug and not bug.is_deleted:
            if item.business_value is not None:
                bug.business_value = item.business_value
            if item.sprint_value is not None:
                bug.sprint_value = item.sprint_value
    await db.commit()


@router.post(
    "/{bug_id}/duplicate", response_model=BugResponse,
    status_code=status.HTTP_201_CREATED, summary="Duplicate a bug"
)
async def duplicate_bug(
    bug_id: UUID,
    payload: BugDuplicateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Bug:
    source = await db.get(Bug, bug_id)
    if not source or source.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")

    titles_res = await db.execute(
        select(Bug.title).where(
            Bug.deliverable_id == source.deliverable_id,
            Bug.is_deleted.is_(False),
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
        select(func.count(Bug.id)).where(
            Bug.deliverable_id == source.deliverable_id,
            Bug.is_deleted.is_(False),
        )
    )

    copy = Bug(
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

    if payload.task_ids:
        task_id_set = set(payload.task_ids)
        tasks_res = await db.execute(
            select(Task)
            .where(Task.bug_id == source.id, Task.is_deleted.is_(False))
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
                    bug_id=copy.id,
                    position=pos,
                ))
                pos += 1

    db.add(AuditLog(
        entity_type="Bug",
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
    "/{bug_id}", response_model=BugResponse,
    summary="Get bug by ID"
)
async def get_bug(
    bug_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Bug:
    bug = await db.get(Bug, bug_id)
    if not bug or bug.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")
    return bug


@router.post(
    "/", response_model=BugResponse, status_code=status.HTTP_201_CREATED,
    summary="Create a bug"
)
async def create_bug(
    payload: BugCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Bug:
    count_res = await db.execute(
        select(func.count(Bug.id)).where(
            Bug.deliverable_id == payload.deliverable_id,
            Bug.is_deleted.is_(False),
        )
    )
    bug = Bug(**payload.model_dump())
    bug.position = count_res.scalar() or 0
    db.add(bug)
    await db.flush()

    db.add(AuditLog(
        entity_type="Bug",
        entity_id=bug.id,
        action=AuditAction.created,
        changed_by=current_user.username,
        changed_at=datetime.now(timezone.utc),
        changes={"title": bug.title},
    ))

    await recalculate_upwards("bug", bug.id, db)
    await db.commit()
    await db.refresh(bug)
    return bug


@router.put(
    "/{bug_id}", response_model=BugResponse,
    summary="Update a bug"
)
async def update_bug(
    bug_id: UUID,
    payload: BugUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Bug:
    bug = await db.get(Bug, bug_id)
    if not bug or bug.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")

    changes: dict = {}
    status_changed = False
    for field, value in payload.model_dump(exclude_unset=True).items():
        old = getattr(bug, field)
        if old != value:
            changes[field] = {"old": str(old), "new": str(value)}
            setattr(bug, field, value)
            if field == "status":
                status_changed = True

    if changes:
        db.add(AuditLog(
            entity_type="Bug",
            entity_id=bug.id,
            action=AuditAction.updated,
            changed_by=current_user.username,
            changed_at=datetime.now(timezone.utc),
            changes=changes,
        ))

    if status_changed:
        await recalculate_upwards("bug", bug.id, db)

    await db.commit()
    await db.refresh(bug)
    return bug


@router.delete(
    "/{bug_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a bug"
)
async def delete_bug(
    bug_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    bug = await db.get(Bug, bug_id)
    if not bug or bug.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")

    bug.is_deleted = True
    bug.deleted_at = datetime.now(timezone.utc)

    db.add(AuditLog(
        entity_type="Bug",
        entity_id=bug.id,
        action=AuditAction.deleted,
        changed_by=current_user.username,
        changed_at=datetime.now(timezone.utc),
        changes={"title": bug.title},
    ))
    await recalculate_upwards("bug", bug.id, db)
    await db.commit()
