"""CRUD router for ProjectGroups."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit_log import AuditAction, AuditLog
from app.models.project_group import ProjectGroup
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.project_group import ProjectGroupCreate, ProjectGroupResponse, ProjectGroupUpdate

router = APIRouter(prefix="/project-groups", tags=["project-groups"])


@router.get("/", response_model=list[ProjectGroupResponse], summary="List all project groups")
async def list_project_groups(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ProjectGroup]:
    result = await db.execute(
        select(ProjectGroup).where(ProjectGroup.is_deleted.is_(False)).order_by(ProjectGroup.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{group_id}", response_model=ProjectGroupResponse, summary="Get a project group by ID")
async def get_project_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ProjectGroup:
    group = await db.get(ProjectGroup, group_id)
    if not group or group.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project group not found")
    return group


@router.post(
    "/", response_model=ProjectGroupResponse, status_code=status.HTTP_201_CREATED,
    summary="Create a project group"
)
async def create_project_group(
    payload: ProjectGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectGroup:
    group = ProjectGroup(**payload.model_dump())
    db.add(group)
    await db.flush()

    audit = AuditLog(
        entity_type="ProjectGroup",
        entity_id=group.id,
        action=AuditAction.created,
        changed_by=current_user.username,
        changed_at=datetime.now(timezone.utc),
        changes={"title": group.title},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(group)
    return group


@router.put("/{group_id}", response_model=ProjectGroupResponse, summary="Update a project group")
async def update_project_group(
    group_id: UUID,
    payload: ProjectGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectGroup:
    group = await db.get(ProjectGroup, group_id)
    if not group or group.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project group not found")

    changes: dict = {}
    for field, value in payload.model_dump(exclude_unset=True).items():
        old = getattr(group, field)
        if old != value:
            changes[field] = {"old": str(old), "new": str(value)}
            setattr(group, field, value)

    if changes:
        audit = AuditLog(
            entity_type="ProjectGroup",
            entity_id=group.id,
            action=AuditAction.updated,
            changed_by=current_user.username,
            changed_at=datetime.now(timezone.utc),
            changes=changes,
        )
        db.add(audit)

    await db.commit()
    await db.refresh(group)
    return group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Soft-delete a project group")
async def delete_project_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    group = await db.get(ProjectGroup, group_id)
    if not group or group.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project group not found")

    group.is_deleted = True
    group.deleted_at = datetime.now(timezone.utc)

    audit = AuditLog(
        entity_type="ProjectGroup",
        entity_id=group.id,
        action=AuditAction.deleted,
        changed_by=current_user.username,
        changed_at=datetime.now(timezone.utc),
        changes={"title": group.title},
    )
    db.add(audit)
    await db.commit()
