"""User model – extended with global_role.

global_role replaces the old boolean is_admin flag and adds the superuser tier.

Migration note: is_admin is kept temporarily for backwards-compat read paths
but will be removed once the frontend is updated.
"""

import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class GlobalRole(str, enum.Enum):
    superuser = "superuser"  # bypasses all permission checks
    admin     = "admin"      # user management + read-all; cannot modify project data
    user      = "user"       # default; access only via project memberships


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    username:        Mapped[str]  = mapped_column(String(100), unique=True, nullable=False, index=True)
    email:           Mapped[str]  = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str]  = mapped_column(String(255), nullable=False)
    full_name:       Mapped[str]  = mapped_column(String(255), nullable=True)
    is_active:       Mapped[bool] = mapped_column(Boolean, default=True,  nullable=False)

    # Kept for backwards compat – mirrors global_role == admin|superuser
    is_admin:        Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    global_role: Mapped[GlobalRole] = mapped_column(
        Enum(GlobalRole, name="globalrole"),
        nullable=False,
        default=GlobalRole.user,
        server_default="user",
        index=True,
    )

    # Relations
    comments:    Mapped[list["Comment"]]           = relationship("Comment",           back_populates="author",      lazy="select")  # noqa: F821
    memberships: Mapped[list["ProjectMembership"]] = relationship("ProjectMembership", back_populates="user",        lazy="selectin")  # noqa: F821
