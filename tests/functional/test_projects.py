"""Integration tests for project visibility / membership filter.

User Story: T - Projektzugriff nur Mitgliedern erlauben
  TS-P1 | Normaler User sieht im Listing nur eigene Projekte
  TS-P2 | Direktzugriff auf fremdes Projekt via ID → 403
  TS-P3 | Superuser sieht alle Projekte
  TS-P4 | Topics aus fremdem Projekt nicht sichtbar (Kaskade)
"""

from __future__ import annotations

import pytest

from utils.api_client import ApiClient
from utils.cleanup import CleanupRegistry


# ── TS-P1 | Normaler User sieht nur eigene Projekte ──────────────────────────

@pytest.mark.asyncio
async def test_regular_user_sees_only_own_projects(
    auth_client: ApiClient,
    cleanup_ids: CleanupRegistry,
    test_project_id: str,
):
    # Create a regular user
    resp = await auth_client.post("/users/", json={
        "username": "ts_p1_user",
        "password": "testpass123",
        "email": "ts_p1_user@test.local",
        "global_role": "user",
    })
    resp.raise_for_status()
    user_id = resp.json()["id"]
    cleanup_ids.add("users", user_id)

    # Login as that user
    user_client = await ApiClient.authenticate("ts_p1_user", "testpass123")

    try:
        # Without membership: no projects visible
        resp = await user_client.get("/projects/")
        assert resp.status_code == 200
        assert resp.json() == [], f"Expected empty list, got: {resp.json()}"

        # Add membership to the test project
        resp = await auth_client.post(
            f"/projects/{test_project_id}/members/",
            json={"user_id": user_id, "role": "viewer"},
        )
        assert resp.status_code == 201, resp.text

        # Now the user should see exactly 1 project
        resp = await user_client.get("/projects/")
        assert resp.status_code == 200
        projects = resp.json()
        assert len(projects) == 1, f"Expected 1 project, got {len(projects)}: {projects}"
        assert projects[0]["id"] == test_project_id
    finally:
        await user_client.aclose()


# ── TS-P2 | Direktzugriff auf fremdes Projekt → 403 ─────────────────────────

@pytest.mark.asyncio
async def test_direct_project_access_blocked_for_non_member(
    auth_client: ApiClient,
    cleanup_ids: CleanupRegistry,
    test_project_id: str,
):
    # Create a regular user with no memberships
    resp = await auth_client.post("/users/", json={
        "username": "ts_p2_user",
        "password": "testpass123",
        "email": "ts_p2_user@test.local",
        "global_role": "user",
    })
    resp.raise_for_status()
    user_id = resp.json()["id"]
    cleanup_ids.add("users", user_id)

    user_client = await ApiClient.authenticate("ts_p2_user", "testpass123")
    try:
        # Direct access to a project the user is not a member of → 403
        resp = await user_client.get(f"/projects/{test_project_id}")
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
    finally:
        await user_client.aclose()


# ── TS-P3 | Superuser sieht alle Projekte ────────────────────────────────────

@pytest.mark.asyncio
async def test_superuser_sees_all_projects(
    auth_client: ApiClient,
    cleanup_ids: CleanupRegistry,
    test_project_id: str,
):
    # auth_client is logged in as admin (superuser) – must see all projects
    resp = await auth_client.get("/projects/")
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.json()]
    assert test_project_id in ids


# ── TS-P4 | Topics aus fremdem Projekt nicht sichtbar (Kaskade) ──────────────

@pytest.mark.asyncio
async def test_topics_of_foreign_project_blocked(
    auth_client: ApiClient,
    cleanup_ids: CleanupRegistry,
    test_project_id: str,
    test_topic_id: str,
):
    # Create a user with no memberships
    resp = await auth_client.post("/users/", json={
        "username": "ts_p4_user",
        "password": "testpass123",
        "email": "ts_p4_user@test.local",
        "global_role": "user",
    })
    resp.raise_for_status()
    user_id = resp.json()["id"]
    cleanup_ids.add("users", user_id)

    user_client = await ApiClient.authenticate("ts_p4_user", "testpass123")
    try:
        # Listing with explicit foreign project_id → 403
        resp = await user_client.get(f"/topics/?project_id={test_project_id}")
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"

        # Direct topic access → 403
        resp = await user_client.get(f"/topics/{test_topic_id}")
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
    finally:
        await user_client.aclose()
