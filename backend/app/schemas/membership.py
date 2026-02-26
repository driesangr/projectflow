"""Pydantic schemas for ProjectMembership and extended User responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.project_membership import ProjectRole
from app.models.user import GlobalRole


# ── User schemas (extended) ──────────────────────────────────────────────────

class UserPublic(BaseModel):
    """Minimal user info safe to embed in other responses."""
    model_config = ConfigDict(from_attributes=True)

    id:        UUID
    username:  str
    full_name: str | None = None
    email:     str


class UserResponse(BaseModel):
    """Full user profile – returned to the user themselves or admins."""
    model_config = ConfigDict(from_attributes=True)

    id:          UUID
    username:    str
    email:       str
    full_name:   str | None = None
    is_active:   bool
    global_role: GlobalRole
    # Kept for backwards compat
    is_admin:    bool
    created_at:  datetime
    updated_at:  datetime


class UserCreate(BaseModel):
    username:    str
    email:       str
    password:    str
    full_name:   str | None = None
    global_role: GlobalRole = GlobalRole.user


class UserUpdate(BaseModel):
    email:       str | None = None
    full_name:   str | None = None
    is_active:   bool | None = None
    global_role: GlobalRole | None = None
    password:    str | None = None


# ── Membership schemas ───────────────────────────────────────────────────────

class MembershipResponse(BaseModel):
    """A project membership entry, with embedded user info."""
    model_config = ConfigDict(from_attributes=True)

    id:         UUID
    project_id: UUID
    role:       ProjectRole
    created_at: datetime
    updated_at: datetime
    user:       UserPublic


class MembershipCreate(BaseModel):
    """Add a user to a project."""
    user_id: UUID
    role:    ProjectRole = ProjectRole.member


class MembershipUpdate(BaseModel):
    """Change the role of an existing member."""
    role: ProjectRole
