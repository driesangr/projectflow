"""Pydantic schemas for Link."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, HttpUrl


class LinkBase(BaseModel):
    url: str
    label: Optional[str] = None
    user_story_id: Optional[UUID] = None
    task_id: Optional[UUID] = None


class LinkCreate(LinkBase):
    pass


class LinkUpdate(BaseModel):
    url: Optional[str] = None
    label: Optional[str] = None


class LinkResponse(LinkBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
