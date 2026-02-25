"""Pydantic schemas for ProjectGroup."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProjectGroupBase(BaseModel):
    title: str
    description: Optional[str] = None


class ProjectGroupCreate(ProjectGroupBase):
    pass


class ProjectGroupUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class ProjectGroupResponse(ProjectGroupBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
