"""Link model – can be attached to a UserStory or a Task."""

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Link(Base, TimestampMixin):
    """No soft-delete – links are hard-deleted."""

    __tablename__ = "links"

    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

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

    # Relations
    user_story: Mapped[Optional["UserStory"]] = relationship(  # noqa: F821
        "UserStory",
        primaryjoin="Link.user_story_id == UserStory.id",
        back_populates="links",
    )
    task: Mapped[Optional["Task"]] = relationship(  # noqa: F821
        "Task",
        primaryjoin="Link.task_id == Task.id",
        back_populates="links",
    )
