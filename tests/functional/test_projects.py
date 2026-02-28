"""Integration tests for project visibility / membership filter.

User Story: User sehen nur die zugewiesenen Projekte
  TS-P1 | Normaler User sieht nur eigene Projekte
  TS-P2 | Admin sieht alle Projekte
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


# ── TS-P2 | Admin sieht alle Projekte ────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_sees_all_projects(
    auth_client: ApiClient,
    cleanup_ids: CleanupRegistry,
    test_project_id: str,
):
    # auth_client is logged in as admin – must see all non-deleted projects
    resp = await auth_client.get("/projects/")
    assert resp.status_code == 200
    projects = resp.json()
    ids = [p["id"] for p in projects]
    # Admin must see the fixture test project among others
    assert test_project_id in ids
