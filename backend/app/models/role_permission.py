"""RolePermission model – defines what each project role can do per artifact type.

Roles (ProjectRole) × ArtifactType = permission matrix entry.
Entries with is_explicit=True were set by an admin directly.
Entries with is_explicit=False were propagated from a parent artifact type.
"""

import enum
import uuid

from sqlalchemy import Boolean, Enum, UniqueConstraint, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.project_membership import ProjectRole


class ArtifactType(str, enum.Enum):
    project_group = "project_group"
    project       = "project"
    topic         = "topic"
    deliverable   = "deliverable"
    user_story    = "user_story"
    task          = "task"


class RolePermission(Base, TimestampMixin):
    __tablename__ = "role_permissions"

    __table_args__ = (
        UniqueConstraint("project_role", "artifact_type", name="uq_role_artifact"),
    )

    project_role: Mapped[ProjectRole] = mapped_column(
        Enum(ProjectRole, name="projectrole"),
        nullable=False,
        index=True,
    )
    artifact_type: Mapped[ArtifactType] = mapped_column(
        Enum(ArtifactType, name="artifacttype"),
        nullable=False,
        index=True,
    )
    can_read: Mapped[bool] = mapped_column(Boolean, default=True,  nullable=False)
    can_write: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_create: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    inherit_to_children: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_explicit: Mapped[bool] = mapped_column(Boolean, default=True,  nullable=False)
