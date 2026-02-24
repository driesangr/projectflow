"""Topic model – belongs to a Project."""

import enum
import uuid
from typing import Optional

from sqlalchemy import Date, Enum, Float, ForeignKey, Integer, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class TopicPriority(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"


class Topic(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "topics"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Used for frontend sorting; higher value = more valuable
    business_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Manual drag-and-drop ordering within the parent project
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    priority: Mapped[TopicPriority] = mapped_column(
        Enum(TopicPriority, name="topicpriority"),
        default=TopicPriority.medium,
        nullable=False,
        index=True,
    )
    # Calculated field – stored for fast reads, updated via maturity service
    maturity_percent: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    planned_start_date: Mapped[Optional[object]] = mapped_column(Date, nullable=True)
    planned_end_date: Mapped[Optional[object]] = mapped_column(Date, nullable=True)
    owner_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Foreign key
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relations
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project", back_populates="topics"
    )
    deliverables: Mapped[list["Deliverable"]] = relationship(  # noqa: F821
        "Deliverable", back_populates="topic", lazy="selectin"
    )
