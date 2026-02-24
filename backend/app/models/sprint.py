"""Sprint model – belongs to a Project."""

import uuid
from typing import Optional

from sqlalchemy import Date, ForeignKey, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class Sprint(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "sprints"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[Optional[object]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[object]] = mapped_column(Date, nullable=True)
    goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Foreign key
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relations
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project", back_populates="sprints"
    )
    user_stories: Mapped[list["UserStory"]] = relationship(  # noqa: F821
        "UserStory", back_populates="sprint", lazy="selectin"
    )
