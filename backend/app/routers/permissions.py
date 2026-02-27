"""
Router: /admin/permissions
==========================

CRUD API for granular role-permission configuration.

Endpoint                                  | Required global role
------------------------------------------|---------------------
GET  /admin/permissions/                  | admin or superuser
GET  /admin/permissions/{role}/{artifact} | admin or superuser
PUT  /admin/permissions/{role}/{artifact} | admin or superuser
DELETE /admin/permissions/{role}/{artifact}| admin or superuser
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_global_admin
from app.database import get_db
from app.models.project_membership import ProjectRole
from app.models.role_permission import ArtifactType, RolePermission
from app.schemas.role_permission import RolePermissionResponse, RolePermissionUpdate
from app.services.permissions_service import (
    clear_propagated_permissions,
    propagate_permissions,
)

router = APIRouter(prefix="/admin/permissions", tags=["permissions"])


@router.get(
    "/",
    response_model=list[RolePermissionResponse],
    summary="List all role-permission entries",
)
async def list_permissions(
    role: Optional[ProjectRole] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_global_admin()),
) -> list[RolePermission]:
    stmt = select(RolePermission)
    if role is not None:
        stmt = stmt.where(RolePermission.project_role == role)
    result = await db.execute(stmt.order_by(RolePermission.project_role, RolePermission.artifact_type))
    return result.scalars().all()


@router.get(
    "/{role}/{artifact_type}",
    response_model=RolePermissionResponse,
    summary="Get a single role-permission entry",
)
async def get_permission(
    role: ProjectRole,
    artifact_type: ArtifactType,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_global_admin()),
) -> RolePermission:
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.project_role == role,
            RolePermission.artifact_type == artifact_type,
        )
    )
    perm = result.scalar_one_or_none()
    if perm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Permission entry not found.")
    return perm


@router.put(
    "/{role}/{artifact_type}",
    response_model=RolePermissionResponse,
    summary="Upsert a role-permission entry",
)
async def upsert_permission(
    role: ProjectRole,
    artifact_type: ArtifactType,
    payload: RolePermissionUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_global_admin()),
) -> RolePermission:
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.project_role == role,
            RolePermission.artifact_type == artifact_type,
        )
    )
    perm = result.scalar_one_or_none()

    prev_inherit = perm.inherit_to_children if perm else False

    if perm is None:
        perm = RolePermission(
            project_role  = role,
            artifact_type = artifact_type,
            can_read      = payload.can_read   if payload.can_read   is not None else True,
            can_write     = payload.can_write  if payload.can_write  is not None else False,
            can_create    = payload.can_create if payload.can_create is not None else False,
            can_delete    = payload.can_delete if payload.can_delete is not None else False,
            inherit_to_children = payload.inherit_to_children if payload.inherit_to_children is not None else False,
            is_explicit   = True,
        )
        db.add(perm)
    else:
        if payload.can_read            is not None: perm.can_read            = payload.can_read
        if payload.can_write           is not None: perm.can_write           = payload.can_write
        if payload.can_create          is not None: perm.can_create          = payload.can_create
        if payload.can_delete          is not None: perm.can_delete          = payload.can_delete
        if payload.inherit_to_children is not None: perm.inherit_to_children = payload.inherit_to_children
        perm.is_explicit = True

    await db.flush()

    # Handle propagation
    if perm.inherit_to_children:
        await propagate_permissions(role, artifact_type, perm, db)
    elif prev_inherit and not perm.inherit_to_children:
        # inherit was turned off → remove previously propagated entries
        await clear_propagated_permissions(role, artifact_type, db)

    await db.commit()
    await db.refresh(perm)
    return perm


@router.delete(
    "/{role}/{artifact_type}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a role-permission entry",
)
async def delete_permission(
    role: ProjectRole,
    artifact_type: ArtifactType,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_global_admin()),
) -> None:
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.project_role == role,
            RolePermission.artifact_type == artifact_type,
        )
    )
    perm = result.scalar_one_or_none()
    if perm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Permission entry not found.")
    await db.delete(perm)
    await db.commit()
