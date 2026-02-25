"""ProjectGroup model."""

from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class ProjectGroup(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "project_groups"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    projects: Mapped[list["Project"]] = relationship(  # noqa: F821
        "Project", back_populates="project_group", lazy="selectin"
    )
