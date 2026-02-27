"""CRUD router for Tasks."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import check_artifact_permission
from app.database import get_db
from app.models.audit_log import AuditAction, AuditLog
from app.models.bug import Bug
from app.models.deliverable import Deliverable
from app.models.role_permission import ArtifactType
from app.models.task import Task
from app.models.topic import Topic
from app.models.user import User
from app.models.user_story import UserStory
from app.routers.auth import get_current_user
from app.schemas.reorder import ReorderItem
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.maturity import recalculate_upwards

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def _resolve_task_project_id(task: Task, db: AsyncSession) -> UUID:
    """Resolve project_id for a task via user_story or bug → deliverable → topic."""
    if task.user_story_id:
        story = await db.get(UserStory, task.user_story_id)
        deliverable = await db.get(Deliverable, story.deliverable_id)
    else:
        bug = await db.get(Bug, task.bug_id)
        deliverable = await db.get(Deliverable, bug.deliverable_id)
    if deliverable.project_id:
        return deliverable.project_id
    topic = await db.get(Topic, deliverable.topic_id)
    return topic.project_id


@router.get("/", response_model=list[TaskResponse], summary="List tasks")
async def list_tasks(
    user_story_id: UUID | None = Query(default=None),
    bug_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Task]:
    query = select(Task).where(Task.is_deleted.is_(False))
    if user_story_id:
        query = query.where(Task.user_story_id == user_story_id)
    if bug_id:
        query = query.where(Task.bug_id == bug_id)
    result = await db.execute(query.order_by(Task.position.asc(), Task.created_at.asc()))
    return result.scalars().all()


@router.patch("/reorder", status_code=status.HTTP_204_NO_CONTENT, summary="Reorder tasks")
async def reorder_tasks(
    items: list[ReorderItem],
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    for item in items:
        task = await db.get(Task, item.id)
        if task and not task.is_deleted:
            task.position = item.position
    await db.commit()


@router.get("/{task_id}", response_model=TaskResponse, summary="Get task by ID")
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    task = await db.get(Task, task_id)
    if not task or task.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    pid = await _resolve_task_project_id(task, db)
    if not await check_artifact_permission(current_user, pid, ArtifactType.task, "read", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied: 'read' on 'task'.")
    return task


@router.post(
    "/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED,
    summary="Create a task"
)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    # Resolve project_id for permission check
    if payload.user_story_id:
        story = await db.get(UserStory, payload.user_story_id)
        deliverable = await db.get(Deliverable, story.deliverable_id)
    else:
        bug = await db.get(Bug, payload.bug_id)
        deliverable = await db.get(Deliverable, bug.deliverable_id)
    if deliverable.project_id:
        pid = deliverable.project_id
    else:
        topic = await db.get(Topic, deliverable.topic_id)
        pid = topic.project_id
    if not await check_artifact_permission(current_user, pid, ArtifactType.task, "create", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied: 'create' on 'task'.")

    # Determine parent for position counting
    if payload.user_story_id:
        count_res = await db.execute(
            select(func.count(Task.id)).where(
                Task.user_story_id == payload.user_story_id,
                Task.is_deleted.is_(False),
            )
        )
    else:
        count_res = await db.execute(
            select(func.count(Task.id)).where(
                Task.bug_id == payload.bug_id,
                Task.is_deleted.is_(False),
            )
        )

    task = Task(**payload.model_dump())
    task.position = count_res.scalar() or 0
    db.add(task)
    await db.flush()

    db.add(AuditLog(
        entity_type="Task",
        entity_id=task.id,
        action=AuditAction.created,
        changed_by=current_user.username,
        changed_at=datetime.now(timezone.utc),
        changes={"title": task.title},
    ))
    await db.commit()
    await db.refresh(task)
    return task


@router.put("/{task_id}", response_model=TaskResponse, summary="Update a task")
async def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    task = await db.get(Task, task_id)
    if not task or task.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    pid = await _resolve_task_project_id(task, db)
    if not await check_artifact_permission(current_user, pid, ArtifactType.task, "write", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied: 'write' on 'task'.")

    changes: dict = {}
    status_changed = False
    for field, value in payload.model_dump(exclude_unset=True).items():
        old = getattr(task, field)
        if old != value:
            changes[field] = {"old": str(old), "new": str(value)}
            setattr(task, field, value)
            if field == "status":
                status_changed = True

    if changes:
        db.add(AuditLog(
            entity_type="Task",
            entity_id=task.id,
            action=AuditAction.updated,
            changed_by=current_user.username,
            changed_at=datetime.now(timezone.utc),
            changes=changes,
        ))

    if status_changed:
        await recalculate_upwards("task", task.id, db)

    await db.commit()
    await db.refresh(task)
    return task


@router.delete(
    "/{task_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a task"
)
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    task = await db.get(Task, task_id)
    if not task or task.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    pid = await _resolve_task_project_id(task, db)
    if not await check_artifact_permission(current_user, pid, ArtifactType.task, "delete", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied: 'delete' on 'task'.")

    task.is_deleted = True
    task.deleted_at = datetime.now(timezone.utc)

    db.add(AuditLog(
        entity_type="Task",
        entity_id=task.id,
        action=AuditAction.deleted,
        changed_by=current_user.username,
        changed_at=datetime.now(timezone.utc),
        changes={"title": task.title},
    ))
    await db.commit()
