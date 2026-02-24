"""Pydantic schemas for Comment."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CommentBase(BaseModel):
    content: str
    user_story_id: Optional[UUID] = None
    task_id: Optional[UUID] = None


class CommentCreate(CommentBase):
    pass


class CommentUpdate(BaseModel):
    content: Optional[str] = None


class CommentResponse(CommentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    author_id: UUID
    created_at: datetime
    updated_at: datetime
