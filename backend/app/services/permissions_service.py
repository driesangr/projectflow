"""
permissions_service.py
======================

Business logic for granular role-permission management.

Covers:
- Artifact hierarchy definition (A-2.2)
- Propagation of permissions to child artifact types (A-2.3)
- Default permission seed data (A-4.1 + A-4.2)
"""

from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_membership import ProjectRole
from app.models.role_permission import ArtifactType, RolePermission


# ── A-2.2: Hierarchy ─────────────────────────────────────────────────────────

ARTIFACT_HIERARCHY: list[str] = [
    "project_group",
    "project",
    "topic",
    "deliverable",
    "user_story",
    "task",
]


def get_children(artifact_type: ArtifactType) -> list[ArtifactType]:
    """Return all artifact types that are subordinate to the given type."""
    try:
        idx = ARTIFACT_HIERARCHY.index(artifact_type.value)
    except ValueError:
        return []
    return [ArtifactType(v) for v in ARTIFACT_HIERARCHY[idx + 1:]]


# ── A-2.3: Propagation ───────────────────────────────────────────────────────

async def propagate_permissions(
    role: ProjectRole,
    artifact_type: ArtifactType,
    source_permission: RolePermission,
    db: AsyncSession,
) -> None:
    """
    Propagate permission values from *source_permission* downward to all
    child artifact types, skipping any that already have an explicit entry.
    """
    for child_type in get_children(artifact_type):
        # Check if an explicit entry already exists for this child
        result = await db.execute(
            select(RolePermission).where(
                RolePermission.project_role == role,
                RolePermission.artifact_type == child_type,
                RolePermission.is_explicit.is_(True),
            )
        )
        if result.scalar_one_or_none():
            continue  # Explicit entry takes priority – skip

        # Check if a propagated entry already exists
        result = await db.execute(
            select(RolePermission).where(
                RolePermission.project_role == role,
                RolePermission.artifact_type == child_type,
                RolePermission.is_explicit.is_(False),
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.can_read           = source_permission.can_read
            existing.can_write          = source_permission.can_write
            existing.can_create         = source_permission.can_create
            existing.can_delete         = source_permission.can_delete
            existing.inherit_to_children = False
        else:
            db.add(RolePermission(
                project_role        = role,
                artifact_type       = child_type,
                can_read            = source_permission.can_read,
                can_write           = source_permission.can_write,
                can_create          = source_permission.can_create,
                can_delete          = source_permission.can_delete,
                inherit_to_children = False,
                is_explicit         = False,
            ))

    await db.flush()


async def clear_propagated_permissions(
    role: ProjectRole,
    artifact_type: ArtifactType,
    db: AsyncSession,
) -> None:
    """Delete all is_explicit=False entries below the given artifact_type."""
    child_types = get_children(artifact_type)
    if not child_types:
        return
    await db.execute(
        delete(RolePermission).where(
            RolePermission.project_role == role,
            RolePermission.artifact_type.in_(child_types),
            RolePermission.is_explicit.is_(False),
        )
    )
    await db.flush()


# ── A-4.1: Default permission data ───────────────────────────────────────────

_ALL = list(ArtifactType)
_UPPER = [ArtifactType.project_group, ArtifactType.project,
          ArtifactType.topic, ArtifactType.deliverable]
_LOWER = [ArtifactType.user_story, ArtifactType.task]

DEFAULT_PERMISSIONS: list[dict[str, Any]] = [
    # owner – full access on everything
    *[
        dict(project_role=ProjectRole.owner, artifact_type=at,
             can_read=True, can_write=True, can_create=True, can_delete=True)
        for at in _ALL
    ],
    # manager – no delete
    *[
        dict(project_role=ProjectRole.manager, artifact_type=at,
             can_read=True, can_write=True, can_create=True, can_delete=False)
        for at in _ALL
    ],
    # member – read-only on upper levels, write on user_story/task
    *[
        dict(project_role=ProjectRole.member, artifact_type=at,
             can_read=True, can_write=False, can_create=False, can_delete=False)
        for at in _UPPER
    ],
    *[
        dict(project_role=ProjectRole.member, artifact_type=at,
             can_read=True, can_write=True, can_create=True, can_delete=False)
        for at in _LOWER
    ],
    # viewer – read only everywhere
    *[
        dict(project_role=ProjectRole.viewer, artifact_type=at,
             can_read=True, can_write=False, can_create=False, can_delete=False)
        for at in _ALL
    ],
]


# ── A-4.2: Seed function ──────────────────────────────────────────────────────

async def seed_default_permissions(
    db: AsyncSession,
    overwrite: bool = False,
) -> int:
    """
    Insert DEFAULT_PERMISSIONS into the database.

    Idempotent: skips entries where an is_explicit=True record already exists,
    unless *overwrite=True*.

    Returns the number of rows inserted or updated.
    """
    count = 0
    for entry in DEFAULT_PERMISSIONS:
        role: ProjectRole = entry["project_role"]
        artifact_type: ArtifactType = entry["artifact_type"]

        # Check for any existing entry (explicit or propagated) to avoid
        # UniqueConstraintError when propagated entries already exist.
        result = await db.execute(
            select(RolePermission).where(
                RolePermission.project_role == role,
                RolePermission.artifact_type == artifact_type,
            )
        )
        existing = result.scalar_one_or_none()

        if existing and not overwrite:
            continue

        if existing:
            existing.can_read            = entry["can_read"]
            existing.can_write           = entry["can_write"]
            existing.can_create          = entry["can_create"]
            existing.can_delete          = entry["can_delete"]
            existing.is_explicit         = True
        else:
            db.add(RolePermission(
                project_role        = role,
                artifact_type       = artifact_type,
                can_read            = entry["can_read"],
                can_write           = entry["can_write"],
                can_create          = entry["can_create"],
                can_delete          = entry["can_delete"],
                inherit_to_children = False,
                is_explicit         = True,
            ))
        count += 1

    await db.commit()
    return count


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import os

    # Allow running from repo root: python -m app.services.permissions_service
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    from app.database import AsyncSessionLocal  # type: ignore

    async def _main() -> None:
        async with AsyncSessionLocal() as session:
            n = await seed_default_permissions(session, overwrite=False)
            print(f"Seeded {n} permission entries.")

    asyncio.run(_main())
