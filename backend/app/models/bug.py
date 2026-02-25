"""Bug model – belongs to a Deliverable, optionally assigned to a Sprint."""

import enum
import uuid
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class BugStatus(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"
    on_hold = "on_hold"


class Bug(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "bugs"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    acceptance_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    story_points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    business_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sprint_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    status: Mapped[BugStatus] = mapped_column(
        Enum(BugStatus, name="bugstatus"),
        default=BugStatus.todo,
        nullable=False,
        index=True,
    )
    owner_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Foreign keys
    deliverable_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deliverables.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sprint_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sprints.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relations
    deliverable: Mapped["Deliverable"] = relationship(  # noqa: F821
        "Deliverable", back_populates="bugs"
    )
    sprint: Mapped[Optional["Sprint"]] = relationship(  # noqa: F821
        "Sprint", back_populates="bugs"
    )
    tasks: Mapped[list["Task"]] = relationship(  # noqa: F821
        "Task", back_populates="bug", lazy="selectin"
    )
    comments: Mapped[list["Comment"]] = relationship(  # noqa: F821
        "Comment",
        primaryjoin="and_(Comment.bug_id == Bug.id)",
        back_populates="bug",
        lazy="selectin",
    )
    links: Mapped[list["Link"]] = relationship(  # noqa: F821
        "Link",
        primaryjoin="and_(Link.bug_id == Bug.id)",
        back_populates="bug",
        lazy="selectin",
    )
