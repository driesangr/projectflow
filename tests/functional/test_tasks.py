"""Integration tests for /tasks endpoints.

D5 | Testszenarien: Tasks
  TS-TK1 | Task erstellen, Status ändern und löschen
"""

from __future__ import annotations

import uuid

import pytest

from utils.api_client import ApiClient
from utils.cleanup import CleanupRegistry


async def _create_story(client: ApiClient, cleanup: CleanupRegistry, deliverable_id: str) -> str:
    """Create a temporary user story and register it for cleanup."""
    resp = await client.post(
        "/user-stories/", json={"title": "Temp Story for Tasks", "deliverable_id": deliverable_id}
    )
    assert resp.status_code == 201
    story_id = resp.json()["id"]
    cleanup.add("user_story", story_id)
    return story_id


# ── TS-TK1.1 | test_create_task + test_task_status_transition ────────────────

@pytest.mark.asyncio
async def test_create_task(
    auth_client: ApiClient, cleanup_ids: CleanupRegistry, test_deliverable_id: str
):
    story_id = await _create_story(auth_client, cleanup_ids, test_deliverable_id)

    payload = {"title": "Test Task", "user_story_id": story_id}
    resp = await auth_client.post("/tasks/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["title"] == "Test Task"
    assert data["user_story_id"] == story_id
    assert data["status"] == "todo"
    assert "id" in data
    cleanup_ids.add("task", data["id"])


@pytest.mark.asyncio
async def test_task_status_transition(
    auth_client: ApiClient, cleanup_ids: CleanupRegistry, test_deliverable_id: str
):
    story_id = await _create_story(auth_client, cleanup_ids, test_deliverable_id)

    # Create task
    resp = await auth_client.post("/tasks/", json={"title": "Status Task", "user_story_id": story_id})
    assert resp.status_code == 201
    task_id = resp.json()["id"]
    cleanup_ids.add("task", task_id)

    # todo → in_progress
    resp = await auth_client.put(f"/tasks/{task_id}", json={"status": "in_progress"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"

    # in_progress → done
    resp = await auth_client.put(f"/tasks/{task_id}", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


# ── TS-TK1.2 | test_delete_task ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_task(
    auth_client: ApiClient, cleanup_ids: CleanupRegistry, test_deliverable_id: str
):
    story_id = await _create_story(auth_client, cleanup_ids, test_deliverable_id)

    # Create task
    resp = await auth_client.post("/tasks/", json={"title": "DeleteMe Task", "user_story_id": story_id})
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    # Delete (soft)
    resp = await auth_client.delete(f"/tasks/{task_id}")
    assert resp.status_code == 204

    # Verify not found
    resp = await auth_client.get(f"/tasks/{task_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_task_not_found(auth_client: ApiClient):
    fake_id = str(uuid.uuid4())
    resp = await auth_client.get(f"/tasks/{fake_id}")
    assert resp.status_code == 404
