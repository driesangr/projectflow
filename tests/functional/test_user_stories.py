"""Integration tests for /user-stories endpoints.

D4 | Testszenarien: User Stories
  TS-US1 | User Story erstellen und Status ändern
"""

from __future__ import annotations

import pytest

from utils.api_client import ApiClient
from utils.cleanup import CleanupRegistry

# Use an existing deliverable as parent (D1 Testframework-Basis)
DELIVERABLE_ID = "45c66486-6320-463e-9108-0bd34d96f83e"


# ── TS-US1.1 | User Story CRUD und Status-Flow ────────────────────────────────

@pytest.mark.asyncio
async def test_create_user_story(auth_client: ApiClient, cleanup_ids: CleanupRegistry):
    payload = {"title": "Test User Story", "deliverable_id": DELIVERABLE_ID}
    resp = await auth_client.post("/user-stories/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["title"] == "Test User Story"
    assert data["deliverable_id"] == DELIVERABLE_ID
    assert data["status"] == "todo"
    assert "id" in data
    cleanup_ids.add("user_story", data["id"])


@pytest.mark.asyncio
async def test_get_user_story(auth_client: ApiClient, cleanup_ids: CleanupRegistry):
    # Create
    resp = await auth_client.post("/user-stories/", json={"title": "GetMe Story", "deliverable_id": DELIVERABLE_ID})
    assert resp.status_code == 201
    story_id = resp.json()["id"]
    cleanup_ids.add("user_story", story_id)

    # Retrieve
    resp = await auth_client.get(f"/user-stories/{story_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == story_id


@pytest.mark.asyncio
async def test_update_user_story_status(auth_client: ApiClient, cleanup_ids: CleanupRegistry):
    # Create
    resp = await auth_client.post("/user-stories/", json={"title": "StatusFlow Story", "deliverable_id": DELIVERABLE_ID})
    assert resp.status_code == 201
    story_id = resp.json()["id"]
    cleanup_ids.add("user_story", story_id)

    # todo → in_progress
    resp = await auth_client.put(f"/user-stories/{story_id}", json={"status": "in_progress"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"

    # in_progress → done
    resp = await auth_client.put(f"/user-stories/{story_id}", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


@pytest.mark.asyncio
async def test_list_user_stories_by_deliverable(auth_client: ApiClient, cleanup_ids: CleanupRegistry):
    # Create
    resp = await auth_client.post("/user-stories/", json={"title": "ListMe Story", "deliverable_id": DELIVERABLE_ID})
    assert resp.status_code == 201
    story_id = resp.json()["id"]
    cleanup_ids.add("user_story", story_id)

    # List
    resp = await auth_client.get("/user-stories/", params={"deliverable_id": DELIVERABLE_ID})
    assert resp.status_code == 200
    ids = [s["id"] for s in resp.json()]
    assert story_id in ids


# ── TS-US1.2 | test_create_user_story_invalid_status ─────────────────────────

@pytest.mark.asyncio
async def test_create_user_story_invalid_status(auth_client: ApiClient):
    payload = {"title": "Bad Status Story", "deliverable_id": DELIVERABLE_ID, "status": "invalid_status"}
    resp = await auth_client.post("/user-stories/", json=payload)
    assert resp.status_code == 422, resp.text
