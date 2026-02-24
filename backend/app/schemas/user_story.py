"""Pydantic schemas for UserStory."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.user_story import UserStoryStatus


class UserStoryBase(BaseModel):
    title: str
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    story_points: Optional[int] = None
    status: UserStoryStatus = UserStoryStatus.todo
    owner_name: Optional[str] = None
    deliverable_id: UUID
    sprint_id: Optional[UUID] = None


class UserStoryCreate(UserStoryBase):
    pass


class UserStoryUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    story_points: Optional[int] = None
    status: Optional[UserStoryStatus] = None
    owner_name: Optional[str] = None
    sprint_id: Optional[UUID] = None


class UserStoryResponse(UserStoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    # Optional nested children for tree view
    tasks: Optional[list["TaskResponse"]] = None  # noqa: F821


# Resolve forward reference
from app.schemas.task import TaskResponse  # noqa: E402

UserStoryResponse.model_rebuild()
