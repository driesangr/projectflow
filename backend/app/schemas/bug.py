"""Pydantic schemas for Bug."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.bug import BugStatus


class BugBase(BaseModel):
    title: str
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    story_points: Optional[int] = None
    business_value: Optional[int] = None
    sprint_value: Optional[int] = None
    status: BugStatus = BugStatus.todo
    owner_name: Optional[str] = None
    deliverable_id: UUID
    sprint_id: Optional[UUID] = None


class BugCreate(BugBase):
    pass


class BugUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    story_points: Optional[int] = None
    business_value: Optional[int] = None
    sprint_value: Optional[int] = None
    status: Optional[BugStatus] = None
    owner_name: Optional[str] = None
    sprint_id: Optional[UUID] = None


class BugDuplicateRequest(BaseModel):
    task_ids: list[UUID] = []


class BugValueItem(BaseModel):
    id: UUID
    business_value: Optional[int] = None
    sprint_value: Optional[int] = None


class BugResponse(BugBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    tasks: Optional[list["TaskResponse"]] = None  # noqa: F821


# Resolve forward reference
from app.schemas.task import TaskResponse  # noqa: E402

BugResponse.model_rebuild()
