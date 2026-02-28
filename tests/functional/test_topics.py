"""Integration tests for /topics endpoints.

D2 | Testszenarien: Topics
  TS-T1 | Topic erstellen (Happy Path + Fehlerfälle)
  TS-T2 | Topic lesen und aktualisieren
  TS-T3 | Topic löschen (Soft-Delete)
"""

from __future__ import annotations

import uuid

import pytest

from utils.api_client import ApiClient
from utils.cleanup import CleanupRegistry


# ── TS-T1.1 | test_create_topic_success ──────────────────────────────────────

@pytest.mark.asyncio
async def test_create_topic_success(
    auth_client: ApiClient, cleanup_ids: CleanupRegistry, test_project_id: str
):
    payload = {"title": "Test-Topic Integration", "project_id": test_project_id}
    resp = await auth_client.post("/topics/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["title"] == "Test-Topic Integration"
    assert data["project_id"] == test_project_id
    assert "id" in data
    cleanup_ids.add("topic", data["id"])


# ── TS-T1.2 | test_create_topic_missing_title + test_create_topic_invalid_project ─

@pytest.mark.asyncio
async def test_create_topic_missing_title(auth_client: ApiClient, test_project_id: str):
    payload = {"project_id": test_project_id}
    resp = await auth_client.post("/topics/", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_topic_invalid_project(auth_client: ApiClient):
    payload = {"title": "Ghost Topic", "project_id": str(uuid.uuid4())}
    resp = await auth_client.post("/topics/", json=payload)
    # FK constraint or permission denied – must not succeed
    assert resp.status_code != 201, resp.text


# ── TS-T2.1 | test_get_topic + test_update_topic ─────────────────────────────

@pytest.mark.asyncio
async def test_get_topic(
    auth_client: ApiClient, cleanup_ids: CleanupRegistry, test_project_id: str
):
    # Create
    resp = await auth_client.post("/topics/", json={"title": "GetMe", "project_id": test_project_id})
    assert resp.status_code == 201
    topic_id = resp.json()["id"]
    cleanup_ids.add("topic", topic_id)

    # Retrieve
    resp = await auth_client.get(f"/topics/{topic_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == topic_id
    assert data["title"] == "GetMe"


@pytest.mark.asyncio
async def test_update_topic(
    auth_client: ApiClient, cleanup_ids: CleanupRegistry, test_project_id: str
):
    # Create
    resp = await auth_client.post("/topics/", json={"title": "UpdateMe", "project_id": test_project_id})
    assert resp.status_code == 201
    topic_id = resp.json()["id"]
    cleanup_ids.add("topic", topic_id)

    # Update
    resp = await auth_client.put(f"/topics/{topic_id}", json={"title": "Updated Title"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Title"


# ── TS-T2.2 | test_get_topic_not_found ───────────────────────────────────────

@pytest.mark.asyncio
async def test_get_topic_not_found(auth_client: ApiClient):
    fake_id = str(uuid.uuid4())
    resp = await auth_client.get(f"/topics/{fake_id}")
    assert resp.status_code == 404


# ── TS-T3.1 | test_delete_topic + test_deleted_topic_not_found ───────────────

@pytest.mark.asyncio
async def test_delete_topic(auth_client: ApiClient, test_project_id: str):
    # Create
    resp = await auth_client.post("/topics/", json={"title": "DeleteMe", "project_id": test_project_id})
    assert resp.status_code == 201
    topic_id = resp.json()["id"]

    # Delete (soft)
    resp = await auth_client.delete(f"/topics/{topic_id}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_deleted_topic_not_found(auth_client: ApiClient, test_project_id: str):
    # Create
    resp = await auth_client.post("/topics/", json={"title": "DeleteAndGet", "project_id": test_project_id})
    assert resp.status_code == 201
    topic_id = resp.json()["id"]

    # Delete
    await auth_client.delete(f"/topics/{topic_id}")

    # Should now return 404
    resp = await auth_client.get(f"/topics/{topic_id}")
    assert resp.status_code == 404
