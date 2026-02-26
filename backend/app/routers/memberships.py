"""
Router: /projects/{project_id}/members
=======================================

Manages the per-project membership list.

Endpoint                                      | Min. role required
----------------------------------------------|--------------------
GET  /projects/{id}/members                   | viewer
POST /projects/{id}/members                   | owner
PUT  /projects/{id}/members/{user_id}         | owner
DELETE /projects/{id}/members/{user_id}       | owner  (cannot remove self if sole owner)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_owner, require_viewer, get_project_role
from app.database import get_db
from app.models.project_membership import ProjectMembership, ProjectRole
from app.models.user import GlobalRole, User
from app.routers.auth import get_current_user
from app.schemas.membership import MembershipCreate, MembershipResponse, MembershipUpdate

router = APIRouter(
    prefix="/projects/{project_id}/members",
    tags=["memberships"],
)


@router.get(
    "/",
    response_model=list[MembershipResponse],
    summary="List all members of a project",
)
async def list_members(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_viewer),
) -> list[ProjectMembership]:
    result = await db.execute(
        select(ProjectMembership).where(ProjectMembership.project_id == project_id)
    )
    return result.scalars().all()


@router.post(
    "/",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a user to a project",
)
async def add_member(
    project_id: UUID,
    payload: MembershipCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_owner),
) -> ProjectMembership:
    # Prevent duplicate
    existing = await db.execute(
        select(ProjectMembership).where(
            ProjectMembership.project_id == project_id,
            ProjectMembership.user_id   == payload.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this project.",
        )

    # Verify target user exists
    target = await db.get(User, payload.user_id)
    if target is None or target.is_deleted:
        raise HTTPException(status_code=404, detail="User not found.")

    membership = ProjectMembership(
        project_id=project_id,
        user_id=payload.user_id,
        role=payload.role,
    )
    db.add(membership)
    await db.commit()
    await db.refresh(membership)
    return membership


@router.put(
    "/{user_id}",
    response_model=MembershipResponse,
    summary="Update a member's role",
)
async def update_member_role(
    project_id: UUID,
    user_id: UUID,
    payload: MembershipUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_owner),
) -> ProjectMembership:
    result = await db.execute(
        select(ProjectMembership).where(
            ProjectMembership.project_id == project_id,
            ProjectMembership.user_id   == user_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found.")

    # Prevent demoting the last owner
    if membership.role == ProjectRole.owner and payload.role != ProjectRole.owner:
        owners = await db.execute(
            select(ProjectMembership).where(
                ProjectMembership.project_id == project_id,
                ProjectMembership.role       == ProjectRole.owner,
            )
        )
        if len(owners.scalars().all()) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last owner of a project.",
            )

    membership.role = payload.role
    await db.commit()
    await db.refresh(membership)
    return membership


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member from a project",
)
async def remove_member(
    project_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_owner),
) -> None:
    result = await db.execute(
        select(ProjectMembership).where(
            ProjectMembership.project_id == project_id,
            ProjectMembership.user_id   == user_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found.")

    # Prevent removing the last owner
    if membership.role == ProjectRole.owner:
        owners = await db.execute(
            select(ProjectMembership).where(
                ProjectMembership.project_id == project_id,
                ProjectMembership.role       == ProjectRole.owner,
            )
        )
        if len(owners.scalars().all()) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last owner of a project.",
            )

    await db.delete(membership)
    await db.commit()
