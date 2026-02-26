"""ProjectMembership model – joins Users to Projects with a role.

Roles (per-project):
    owner   – full control, can manage members, delete project
    manager – can create/edit all items, cannot delete project or manage members
    member  – can create and edit items assigned to them; cannot delete
    viewer  – read-only access

Global roles live on User.global_role:
    superuser – bypasses all project-level permission checks
    admin     – can manage users and see all projects; cannot modify data
    user      – default; access only via project memberships
"""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ProjectRole(str, enum.Enum):
    owner   = "owner"
    manager = "manager"
    member  = "member"
    viewer  = "viewer"


class ProjectMembership(Base, TimestampMixin):
    __tablename__ = "project_memberships"

    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="uq_membership_user_project"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[ProjectRole] = mapped_column(
        Enum(ProjectRole, name="projectrole"),
        nullable=False,
        default=ProjectRole.member,
    )

    # Relations
    user:    Mapped["User"]    = relationship("User",    back_populates="memberships")   # noqa: F821
    project: Mapped["Project"] = relationship("Project", back_populates="memberships")  # noqa: F821
