"""
app/core/permissions.py
=======================

Centralised permission helpers for ProjectFlow.

Permission model
----------------
Every user has a **global role** (on User.global_role):

    superuser  – bypasses *all* checks; can do everything everywhere
    admin      – can manage users and read all projects; cannot mutate
                 project data unless also a project member
    user       – default; access only through project memberships

Every project has **per-project memberships** (ProjectMembership.role):

    owner      – full CRUD + member management + project deletion
    manager    – full CRUD on project content; no member management
    member     – create / edit items; cannot delete project-level entities
    viewer     – read-only

Decision matrix
---------------
Action                        | superuser | admin | owner | manager | member | viewer
------------------------------|-----------|-------|-------|---------|--------|-------
Read project + contents       |    ✓      |   ✓   |   ✓   |    ✓    |   ✓    |   ✓
Create / edit project items   |    ✓      |   –   |   ✓   |    ✓    |   ✓    |   –
Delete project items          |    ✓      |   –   |   ✓   |    ✓    |   –    |   –
Manage members                |    ✓      |   –   |   ✓   |    –    |   –    |   –
Delete project                |    ✓      |   –   |   ✓   |    –    |   –    |   –
Manage all users              |    ✓      |   ✓   |   –   |    –    |   –    |   –
"""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.project_membership import ProjectMembership, ProjectRole
from app.models.user import GlobalRole, User
from app.routers.auth import get_current_user


# ── Tier ordering (higher index = more powerful) ─────────────────────────────

_PROJECT_ROLE_ORDER = [
    ProjectRole.viewer,
    ProjectRole.member,
    ProjectRole.manager,
    ProjectRole.owner,
]


def _project_role_gte(role: ProjectRole, minimum: ProjectRole) -> bool:
    return _PROJECT_ROLE_ORDER.index(role) >= _PROJECT_ROLE_ORDER.index(minimum)


# ── Low-level helper ─────────────────────────────────────────────────────────

async def get_project_role(
    user: User,
    project_id: UUID,
    db: AsyncSession,
) -> ProjectRole | None:
    """Return the user's project-level role, or None if not a member."""
    result = await db.execute(
        select(ProjectMembership).where(
            ProjectMembership.user_id   == user.id,
            ProjectMembership.project_id == project_id,
        )
    )
    membership = result.scalar_one_or_none()
    return membership.role if membership else None


# ── Reusable dependency factories ────────────────────────────────────────────

def require_project_role(minimum_role: ProjectRole):
    """
    FastAPI dependency factory.

    Usage::

        @router.post("/projects/{project_id}/topics")
        async def create_topic(
            project_id: UUID,
            ...
            _: None = Depends(require_project_role(ProjectRole.member)),
        ):
            ...

    Superusers always pass.  Admins pass for read-only (viewer) checks only.
    """
    async def dependency(
        project_id: UUID,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        # Superuser bypasses everything
        if current_user.global_role == GlobalRole.superuser:
            return current_user

        # Admin may read but not write
        if current_user.global_role == GlobalRole.admin:
            if minimum_role == ProjectRole.viewer:
                return current_user
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admins have read-only access to project data.",
            )

        role = await get_project_role(current_user, project_id, db)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this project.",
            )
        if not _project_role_gte(role, minimum_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires at least the '{minimum_role.value}' role.",
            )
        return current_user

    return dependency


def require_global_admin():
    """Dependency: user must be admin or superuser."""
    async def dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.global_role not in (GlobalRole.admin, GlobalRole.superuser):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or superuser role required.",
            )
        return current_user

    return dependency


def require_superuser():
    """Dependency: user must be superuser."""
    async def dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.global_role != GlobalRole.superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Superuser role required.",
            )
        return current_user

    return dependency


# ── Convenience shortcuts (pre-built dependencies) ───────────────────────────

require_viewer  = require_project_role(ProjectRole.viewer)
require_member  = require_project_role(ProjectRole.member)
require_manager = require_project_role(ProjectRole.manager)
require_owner   = require_project_role(ProjectRole.owner)
