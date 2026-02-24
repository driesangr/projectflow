"""CRUD router for Tasks."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit_log import AuditAction, AuditLog
from app.models.task import Task
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.maturity import recalculate_upwards

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=list[TaskResponse], summary="List tasks")
async def list_tasks(
    user_story_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Task]:
    query = select(Task).where(Task.is_deleted.is_(False))
    if user_story_id:
        query = query.where(Task.user_story_id == user_story_id)
    result = await db.execute(query.order_by(Task.created_at.desc()))
    return result.scalars().all()


@router.get("/{task_id}", response_model=TaskResponse, summary="Get task by ID")
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Task:
    task = await db.get(Task, task_id)
    if not task or task.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
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
    task = Task(**payload.model_dump())
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

    # Task status change triggers upward maturity recalculation
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
