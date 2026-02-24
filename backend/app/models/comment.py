"""Comment model – can be attached to a UserStory or a Task."""

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Comment(Base, TimestampMixin):
    """No soft-delete – comments are hard-deleted."""

    __tablename__ = "comments"

    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Exactly one of the two FKs should be set
    user_story_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_stories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relations
    user_story: Mapped[Optional["UserStory"]] = relationship(  # noqa: F821
        "UserStory",
        primaryjoin="Comment.user_story_id == UserStory.id",
        back_populates="comments",
    )
    task: Mapped[Optional["Task"]] = relationship(  # noqa: F821
        "Task",
        primaryjoin="Comment.task_id == Task.id",
        back_populates="comments",
    )
    author: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="comments"
    )
