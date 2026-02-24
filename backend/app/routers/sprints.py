"""CRUD router for Sprints."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit_log import AuditAction, AuditLog
from app.models.sprint import Sprint
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.sprint import SprintCreate, SprintResponse, SprintUpdate

router = APIRouter(prefix="/sprints", tags=["sprints"])


@router.get("/", response_model=list[SprintResponse], summary="List sprints")
async def list_sprints(
    project_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Sprint]:
    query = select(Sprint).where(Sprint.is_deleted.is_(False))
    if project_id:
        query = query.where(Sprint.project_id == project_id)
    result = await db.execute(query.order_by(Sprint.start_date))
    return result.scalars().all()


@router.get("/{sprint_id}", response_model=SprintResponse, summary="Get sprint by ID")
async def get_sprint(
    sprint_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Sprint:
    sprint = await db.get(Sprint, sprint_id)
    if not sprint or sprint.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found")
    return sprint


@router.post(
    "/", response_model=SprintResponse, status_code=status.HTTP_201_CREATED,
    summary="Create a sprint"
)
async def create_sprint(
    payload: SprintCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Sprint:
    sprint = Sprint(**payload.model_dump())
    db.add(sprint)
    await db.flush()

    db.add(AuditLog(
        entity_type="Sprint",
        entity_id=sprint.id,
        action=AuditAction.created,
        changed_by=current_user.username,
        changed_at=datetime.now(timezone.utc),
        changes={"name": sprint.name},
    ))
    await db.commit()
    await db.refresh(sprint)
    return sprint


@router.put("/{sprint_id}", response_model=SprintResponse, summary="Update a sprint")
async def update_sprint(
    sprint_id: UUID,
    payload: SprintUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Sprint:
    sprint = await db.get(Sprint, sprint_id)
    if not sprint or sprint.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found")

    changes: dict = {}
    for field, value in payload.model_dump(exclude_unset=True).items():
        old = getattr(sprint, field)
        if old != value:
            changes[field] = {"old": str(old), "new": str(value)}
            setattr(sprint, field, value)

    if changes:
        db.add(AuditLog(
            entity_type="Sprint",
            entity_id=sprint.id,
            action=AuditAction.updated,
            changed_by=current_user.username,
            changed_at=datetime.now(timezone.utc),
            changes=changes,
        ))

    await db.commit()
    await db.refresh(sprint)
    return sprint


@router.delete("/{sprint_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Soft-delete a sprint")
async def delete_sprint(
    sprint_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    sprint = await db.get(Sprint, sprint_id)
    if not sprint or sprint.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found")

    sprint.is_deleted = True
    sprint.deleted_at = datetime.now(timezone.utc)

    db.add(AuditLog(
        entity_type="Sprint",
        entity_id=sprint.id,
        action=AuditAction.deleted,
        changed_by=current_user.username,
        changed_at=datetime.now(timezone.utc),
        changes={"name": sprint.name},
    ))
    await db.commit()
