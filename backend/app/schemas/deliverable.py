"""Pydantic schemas for Deliverable."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.deliverable import DeliverableStatus


class DeliverableBase(BaseModel):
    title: str
    description: Optional[str] = None
    epic_points: Optional[int] = None
    status: DeliverableStatus = DeliverableStatus.todo
    owner_name: Optional[str] = None
    topic_id: UUID


class DeliverableCreate(DeliverableBase):
    pass


class DeliverableUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    epic_points: Optional[int] = None
    status: Optional[DeliverableStatus] = None
    owner_name: Optional[str] = None


class DeliverableResponse(DeliverableBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    maturity_percent: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    # Optional nested children for tree view
    user_stories: Optional[list["UserStoryResponse"]] = None  # noqa: F821


# Resolve forward reference
from app.schemas.user_story import UserStoryResponse  # noqa: E402

DeliverableResponse.model_rebuild()
