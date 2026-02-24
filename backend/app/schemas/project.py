"""Pydantic schemas for Project."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.project import MaturityLevel, ProjectStatus


class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    maturity_level: MaturityLevel = MaturityLevel.idea
    status: ProjectStatus = ProjectStatus.active
    owner_name: Optional[str] = None
    tags: Optional[list[str]] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    maturity_level: Optional[MaturityLevel] = None
    status: Optional[ProjectStatus] = None
    owner_name: Optional[str] = None
    tags: Optional[list[str]] = None


class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    # Optional nested children for tree view
    topics: Optional[list["TopicResponse"]] = None  # noqa: F821


# Resolve forward reference after TopicResponse is defined
from app.schemas.topic import TopicResponse  # noqa: E402

ProjectResponse.model_rebuild()
