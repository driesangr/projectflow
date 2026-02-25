"""Deliverable model – belongs to a Topic."""

import enum
import uuid
from typing import Optional

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class DeliverableStatus(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"
    on_hold = "on_hold"


class Deliverable(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "deliverables"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    epic_points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    business_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Manual drag-and-drop ordering within the parent topic
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    # Calculated field – updated via maturity service
    maturity_percent: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    status: Mapped[DeliverableStatus] = mapped_column(
        Enum(DeliverableStatus, name="deliverablestatus"),
        default=DeliverableStatus.todo,
        nullable=False,
        index=True,
    )
    owner_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Foreign key
    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relations
    topic: Mapped["Topic"] = relationship(  # noqa: F821
        "Topic", back_populates="deliverables"
    )
    user_stories: Mapped[list["UserStory"]] = relationship(  # noqa: F821
        "UserStory", back_populates="deliverable", lazy="selectin"
    )
    bugs: Mapped[list["Bug"]] = relationship(  # noqa: F821
        "Bug", back_populates="deliverable", lazy="selectin"
    )
