"""Shared schema for bulk-reorder endpoints."""

from uuid import UUID

from pydantic import BaseModel


class ReorderItem(BaseModel):
    id: UUID
    position: int
