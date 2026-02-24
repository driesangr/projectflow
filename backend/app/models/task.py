"""Task model – belongs to a UserStory."""

import enum
import uuid
from typing import Optional

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class TaskStatus(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class Task(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="taskstatus"),
        default=TaskStatus.todo,
        nullable=False,
        index=True,
    )
    effort_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sprint_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Manual drag-and-drop ordering within the parent user story
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    owner_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Foreign key
    user_story_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_stories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relations
    user_story: Mapped["UserStory"] = relationship(  # noqa: F821
        "UserStory", back_populates="tasks"
    )
    comments: Mapped[list["Comment"]] = relationship(  # noqa: F821
        "Comment",
        primaryjoin="and_(Comment.task_id == Task.id)",
        back_populates="task",
        lazy="selectin",
    )
    links: Mapped[list["Link"]] = relationship(  # noqa: F821
        "Link",
        primaryjoin="and_(Link.task_id == Task.id)",
        back_populates="task",
        lazy="selectin",
    )
