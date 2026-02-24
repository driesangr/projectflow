"""UserStory model – belongs to a Deliverable, optionally assigned to a Sprint."""

import enum
import uuid
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class UserStoryStatus(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"
    on_hold = "on_hold"


class UserStory(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "user_stories"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    acceptance_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    story_points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[UserStoryStatus] = mapped_column(
        Enum(UserStoryStatus, name="userstorystatus"),
        default=UserStoryStatus.todo,
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
    # Optional sprint assignment
    sprint_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sprints.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relations
    deliverable: Mapped["Deliverable"] = relationship(  # noqa: F821
        "Deliverable", back_populates="user_stories"
    )
    sprint: Mapped[Optional["Sprint"]] = relationship(  # noqa: F821
        "Sprint", back_populates="user_stories"
    )
    tasks: Mapped[list["Task"]] = relationship(  # noqa: F821
        "Task", back_populates="user_story", lazy="select"
    )
    comments: Mapped[list["Comment"]] = relationship(  # noqa: F821
        "Comment",
        primaryjoin="and_(Comment.user_story_id == UserStory.id)",
        back_populates="user_story",
        lazy="select",
    )
    links: Mapped[list["Link"]] = relationship(  # noqa: F821
        "Link",
        primaryjoin="and_(Link.user_story_id == UserStory.id)",
        back_populates="user_story",
        lazy="select",
    )
