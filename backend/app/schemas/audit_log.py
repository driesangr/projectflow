"""Pydantic schemas for AuditLog."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.audit_log import AuditAction


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entity_type: str
    entity_id: UUID
    action: AuditAction
    changed_by: str
    changed_at: datetime
    changes: Optional[dict[str, Any]] = None
