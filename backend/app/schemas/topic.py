"""Pydantic schemas for Topic."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.topic import TopicPriority


class TopicBase(BaseModel):
    title: str
    description: Optional[str] = None
    business_value: Optional[int] = None
    priority: TopicPriority = TopicPriority.medium
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    owner_name: Optional[str] = None
    project_id: UUID


class TopicCreate(TopicBase):
    pass


class TopicUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    business_value: Optional[int] = None
    priority: Optional[TopicPriority] = None
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    owner_name: Optional[str] = None


class TopicResponse(TopicBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    maturity_percent: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    # Optional nested children for tree view
    deliverables: Optional[list["DeliverableResponse"]] = None  # noqa: F821


# Resolve forward reference
from app.schemas.deliverable import DeliverableResponse  # noqa: E402

TopicResponse.model_rebuild()
