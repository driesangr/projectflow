"""Project model."""

import enum
import uuid
from typing import Optional

from sqlalchemy import UUID, Enum, ForeignKey, String, Text, Date
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

    # Parent relation
    project_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_groups.id"), nullable=True, index=True
    )
    project_group: Mapped[Optional["ProjectGroup"]] = relationship(  # noqa: F821
        "ProjectGroup", back_populates="projects"
    )

    # Child relations
    topics: Mapped[list["Topic"]] = relationship(  # noqa: F821
        "Topic", back_populates="project", lazy="selectin"
    )
    sprints: Mapped[list["Sprint"]] = relationship(  # noqa: F821
        "Sprint", back_populates="project", lazy="selectin"
    )
    direct_deliverables: Mapped[list["Deliverable"]] = relationship(  # noqa: F821
        "Deliverable",
        back_populates="project",
        lazy="selectin",
        primaryjoin="Deliverable.project_id == Project.id",
        foreign_keys="[Deliverable.project_id]",
    )
