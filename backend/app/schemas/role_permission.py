"""Pydantic schemas for RolePermission."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.project_membership import ProjectRole
from app.models.role_permission import ArtifactType


class RolePermissionBase(BaseModel):
    can_read:            Optional[bool] = None
    can_write:           Optional[bool] = None
    can_create:          Optional[bool] = None
    can_delete:          Optional[bool] = None
    inherit_to_children: Optional[bool] = None


class RolePermissionCreate(RolePermissionBase):
    project_role:  ProjectRole
    artifact_type: ArtifactType


class RolePermissionUpdate(RolePermissionBase):
    pass


class RolePermissionResponse(RolePermissionBase):
    model_config = ConfigDict(from_attributes=True)

    id:                  UUID
    project_role:        ProjectRole
    artifact_type:       ArtifactType
    can_read:            bool
    can_write:           bool
    can_create:          bool
    can_delete:          bool
    inherit_to_children: bool
    is_explicit:         bool
    created_at:          datetime
    updated_at:          datetime
