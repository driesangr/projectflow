"""Integration tests for /deliverables endpoints.

D3 | Testszenarien: Deliverables
  TS-D1 | Deliverable erstellen und lesen
  TS-D2 | Deliverable aktualisieren und löschen
"""

from __future__ import annotations

import uuid

import pytest

from utils.api_client import ApiClient
from utils.cleanup import CleanupRegistry


# ── TS-D1.1 | test_create_deliverable + test_list_deliverables_by_topic ───────

@pytest.mark.asyncio
async def test_create_deliverable(
    auth_client: ApiClient, cleanup_ids: CleanupRegistry, test_topic_id: str
):
    payload = {"title": "Test-Deliverable", "topic_id": test_topic_id}
    resp = await auth_client.post("/deliverables/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["title"] == "Test-Deliverable"
    assert "id" in data
    cleanup_ids.add("deliverable", data["id"])


@pytest.mark.asyncio
async def test_list_deliverables_by_topic(
    auth_client: ApiClient, cleanup_ids: CleanupRegistry, test_topic_id: str
):
    # Create a deliverable first
    payload = {"title": "ListMe Deliverable", "topic_id": test_topic_id}
    resp = await auth_client.post("/deliverables/", json=payload)
    assert resp.status_code == 201
    created_id = resp.json()["id"]
    cleanup_ids.add("deliverable", created_id)

    # List by topic
    resp = await auth_client.get("/deliverables/", params={"topic_id": test_topic_id})
    assert resp.status_code == 200
    ids = [d["id"] for d in resp.json()]
    assert created_id in ids


# ── TS-D1.2 | test_create_deliverable_missing_topic_id ───────────────────────

@pytest.mark.asyncio
async def test_create_deliverable_missing_topic_id(auth_client: ApiClient):
    # Neither topic_id nor project_id provided → validation error
    payload = {"title": "No Parent"}
    resp = await auth_client.post("/deliverables/", json=payload)
    assert resp.status_code == 422, resp.text


# ── TS-D2.1 | test_update_deliverable + test_delete_deliverable + test_update_nonexistent ─

@pytest.mark.asyncio
async def test_update_deliverable(
    auth_client: ApiClient, cleanup_ids: CleanupRegistry, test_topic_id: str
):
    # Create
    resp = await auth_client.post("/deliverables/", json={"title": "UpdateMe", "topic_id": test_topic_id})
    assert resp.status_code == 201
    deliverable_id = resp.json()["id"]
    cleanup_ids.add("deliverable", deliverable_id)

    # Update
    resp = await auth_client.put(f"/deliverables/{deliverable_id}", json={"title": "Updated Deliverable"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Deliverable"


@pytest.mark.asyncio
async def test_delete_deliverable(auth_client: ApiClient, test_topic_id: str):
    # Create
    resp = await auth_client.post("/deliverables/", json={"title": "DeleteMe", "topic_id": test_topic_id})
    assert resp.status_code == 201
    deliverable_id = resp.json()["id"]

    # Delete (soft)
    resp = await auth_client.delete(f"/deliverables/{deliverable_id}")
    assert resp.status_code == 204

    # Verify not found
    resp = await auth_client.get(f"/deliverables/{deliverable_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_nonexistent_deliverable(auth_client: ApiClient):
    fake_id = str(uuid.uuid4())
    resp = await auth_client.put(f"/deliverables/{fake_id}", json={"title": "Ghost"})
    assert resp.status_code == 404
