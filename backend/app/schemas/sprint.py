"""Pydantic schemas for Sprint."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SprintBase(BaseModel):
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    goal: Optional[str] = None
    project_id: UUID


class SprintCreate(SprintBase):
    pass


class SprintUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    goal: Optional[str] = None


class SprintResponse(SprintBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
