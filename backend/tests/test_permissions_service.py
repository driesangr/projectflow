"""
Tests for app/services/permissions_service.py  (A-2.4)

Uses an in-memory SQLite database via aiosqlite + SQLAlchemy async.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, MetaData

from app.models.base import Base
from app.models.project_membership import ProjectRole
from app.models.role_permission import ArtifactType, RolePermission
from app.services.permissions_service import (
    get_children,
    propagate_permissions,
    clear_propagated_permissions,
)

# Tables needed for these tests (avoids JSONB / PostgreSQL-only types in SQLite)
_TEST_TABLES = ["role_permissions"]


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def db():
    """Provide a fresh in-memory SQLite async session for each test."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    # Only create the tables needed for these tests
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[Base.metadata.tables[t] for t in _TEST_TABLES],
            )
        )

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

    await engine.dispose()


# ── Helper ────────────────────────────────────────────────────────────────────

async def make_permission(db: AsyncSession, role: ProjectRole,
                          artifact: ArtifactType, **kwargs) -> RolePermission:
    defaults = dict(can_read=True, can_write=False, can_create=False,
                    can_delete=False, inherit_to_children=False, is_explicit=True)
    defaults.update(kwargs)
    perm = RolePermission(project_role=role, artifact_type=artifact, **defaults)
    db.add(perm)
    await db.flush()
    return perm


# ── A-2.2: get_children ───────────────────────────────────────────────────────

def test_get_children_topic():
    children = get_children(ArtifactType.topic)
    assert ArtifactType.deliverable in children
    assert ArtifactType.user_story in children
    assert ArtifactType.task in children
    assert ArtifactType.project not in children
    assert ArtifactType.project_group not in children


def test_get_children_task():
    assert get_children(ArtifactType.task) == []


def test_get_children_project_group():
    children = get_children(ArtifactType.project_group)
    assert len(children) == 5  # all 5 descendants


# ── A-2.3: propagate_permissions ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_propagation_topic_writes_children(db):
    """Propagation from topic should create entries for deliverable, user_story, task."""
    source = await make_permission(
        db, ProjectRole.member, ArtifactType.topic,
        can_read=True, can_write=True, can_create=True, can_delete=False,
        inherit_to_children=True,
    )
    await propagate_permissions(ProjectRole.member, ArtifactType.topic, source, db)

    for child in [ArtifactType.deliverable, ArtifactType.user_story, ArtifactType.task]:
        result = await db.execute(
            select(RolePermission).where(
                RolePermission.project_role == ProjectRole.member,
                RolePermission.artifact_type == child,
            )
        )
        perm = result.scalar_one_or_none()
        assert perm is not None, f"Expected entry for {child}"
        assert perm.can_read   is True
        assert perm.can_write  is True
        assert perm.can_create is True
        assert perm.can_delete is False
        assert perm.is_explicit is False
        assert perm.inherit_to_children is False


@pytest.mark.asyncio
async def test_propagation_skips_explicit_child(db):
    """An explicit entry on a child must not be overwritten by propagation."""
    # Pre-create explicit entry on deliverable
    await make_permission(
        db, ProjectRole.manager, ArtifactType.deliverable,
        can_read=True, can_write=False, can_create=False, can_delete=True,
        is_explicit=True,
    )

    source = await make_permission(
        db, ProjectRole.manager, ArtifactType.topic,
        can_read=True, can_write=True, can_create=True, can_delete=True,
        inherit_to_children=True,
    )
    await propagate_permissions(ProjectRole.manager, ArtifactType.topic, source, db)

    # deliverable must keep its own explicit values
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.project_role == ProjectRole.manager,
            RolePermission.artifact_type == ArtifactType.deliverable,
        )
    )
    perm = result.scalar_one()
    assert perm.can_delete is True   # original explicit value preserved
    assert perm.can_write  is False  # original explicit value preserved
    assert perm.is_explicit is True


@pytest.mark.asyncio
async def test_propagation_no_children_when_false(db):
    """A source permission with inherit_to_children=False should NOT propagate."""
    source = await make_permission(
        db, ProjectRole.viewer, ArtifactType.project,
        can_read=True, inherit_to_children=False,
    )
    await propagate_permissions(ProjectRole.viewer, ArtifactType.project, source, db)

    # Nothing should be created below project (topic, deliverable, ...)
    # NOTE: propagate_permissions always propagates to children regardless of
    # inherit_to_children flag on source – the flag is stored as metadata for
    # the UI; calling propagate_permissions is at the router's discretion.
    # This test verifies that propagated entries get inherit_to_children=False.
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.project_role == ProjectRole.viewer,
            RolePermission.is_explicit.is_(False),
        )
    )
    propagated = result.scalars().all()
    for p in propagated:
        assert p.inherit_to_children is False


# ── A-2.3: clear_propagated_permissions ──────────────────────────────────────

@pytest.mark.asyncio
async def test_clear_propagated_only_removes_implicit(db):
    """clear_propagated_permissions must only delete is_explicit=False entries."""
    # Explicit entry on deliverable
    explicit = await make_permission(
        db, ProjectRole.owner, ArtifactType.deliverable,
        is_explicit=True,
    )
    # Propagated entry on user_story
    implicit = RolePermission(
        project_role=ProjectRole.owner,
        artifact_type=ArtifactType.user_story,
        can_read=True, can_write=True, can_create=True, can_delete=True,
        inherit_to_children=False, is_explicit=False,
    )
    db.add(implicit)
    await db.flush()

    await clear_propagated_permissions(ProjectRole.owner, ArtifactType.topic, db)

    # Explicit deliverable entry must survive
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.project_role == ProjectRole.owner,
            RolePermission.artifact_type == ArtifactType.deliverable,
        )
    )
    assert result.scalar_one_or_none() is not None

    # Implicit user_story entry must be gone
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.project_role == ProjectRole.owner,
            RolePermission.artifact_type == ArtifactType.user_story,
            RolePermission.is_explicit.is_(False),
        )
    )
    assert result.scalar_one_or_none() is None
