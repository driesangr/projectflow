"""CRUD router for Projects."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import check_artifact_permission, require_artifact_permission
from app.database import get_db
from app.models.audit_log import AuditAction, AuditLog
from app.models.project import Project
from app.models.role_permission import ArtifactType
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectResponse], summary="List all projects")
async def list_projects(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Project]:
    result = await db.execute(
        select(Project).where(Project.is_deleted.is_(False)).order_by(Project.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectResponse, summary="Get a project by ID")
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_artifact_permission(ArtifactType.project, "read")),
) -> Project:
    project = await db.get(Project, project_id)
    if not project or project.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post(
    "/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED,
    summary="Create a project"
)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project = Project(**payload.model_dump())
    db.add(project)
    await db.flush()

    audit = AuditLog(
        entity_type="Project",
        entity_id=project.id,
        action=AuditAction.created,
        changed_by=current_user.username,
        changed_at=datetime.now(timezone.utc),
        changes={"title": project.title},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(project)
    return project


@router.put("/{project_id}", response_model=ProjectResponse, summary="Update a project")
async def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_artifact_permission(ArtifactType.project, "write")),
) -> Project:
    project = await db.get(Project, project_id)
    if not project or project.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    changes: dict = {}
    for field, value in payload.model_dump(exclude_unset=True).items():
        old = getattr(project, field)
        if old != value:
            changes[field] = {"old": str(old), "new": str(value)}
            setattr(project, field, value)

    if changes:
        audit = AuditLog(
            entity_type="Project",
            entity_id=project.id,
            action=AuditAction.updated,
            changed_by=current_user.username,
            changed_at=datetime.now(timezone.utc),
            changes=changes,
        )
        db.add(audit)

    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Soft-delete a project")
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_artifact_permission(ArtifactType.project, "delete")),
) -> None:
    project = await db.get(Project, project_id)
    if not project or project.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    project.is_deleted = True
    project.deleted_at = datetime.now(timezone.utc)

    audit = AuditLog(
        entity_type="Project",
        entity_id=project.id,
        action=AuditAction.deleted,
        changed_by=current_user.username,
        changed_at=datetime.now(timezone.utc),
        changes={"title": project.title},
    )
    db.add(audit)
    await db.commit()
