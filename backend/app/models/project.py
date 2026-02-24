"""Project model."""

import enum
from typing import Optional

from sqlalchemy import Enum, String, Text, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class MaturityLevel(str, enum.Enum):
    idea = "idea"
    concept = "concept"
    in_planning = "in_planning"
    in_progress = "in_progress"
    completed = "completed"
    on_hold = "on_hold"


class ProjectStatus(str, enum.Enum):
    active = "active"
    on_hold = "on_hold"
    completed = "completed"
    cancelled = "cancelled"


class Project(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "projects"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_date: Mapped[Optional[object]] = mapped_column(Date, nullable=True)
    planned_end_date: Mapped[Optional[object]] = mapped_column(Date, nullable=True)
    maturity_level: Mapped[MaturityLevel] = mapped_column(
        Enum(MaturityLevel, name="maturitylevel"),
        default=MaturityLevel.idea,
        nullable=False,
        index=True,
    )
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="projectstatus"),
        default=ProjectStatus.active,
        nullable=False,
        index=True,
    )
    owner_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Stored as a JSON array of strings
    tags: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Child relations
    topics: Mapped[list["Topic"]] = relationship(  # noqa: F821
        "Topic", back_populates="project", lazy="select"
    )
    sprints: Mapped[list["Sprint"]] = relationship(  # noqa: F821
        "Sprint", back_populates="project", lazy="select"
    )
