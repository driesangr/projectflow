"""Shared pytest fixtures for ProjectFlow integration tests."""

from __future__ import annotations

import pytest_asyncio

from utils.api_client import ApiClient
from utils.cleanup import CleanupRegistry


@pytest_asyncio.fixture(scope="session")
async def auth_client():
    """Session-scoped authenticated HTTP client."""
    client = await ApiClient.authenticate()
    yield client
    await client.aclose()


@pytest_asyncio.fixture(scope="session")
async def test_project_id(auth_client: ApiClient) -> str:
    """Create a dedicated test project for the session; soft-delete it afterwards."""
    resp = await auth_client.post("/projects/", json={"title": "Test-Projekt [autotest]"})
    resp.raise_for_status()
    project_id = resp.json()["id"]
    yield project_id
    await auth_client.delete(f"/projects/{project_id}")


@pytest_asyncio.fixture(scope="session")
async def test_topic_id(auth_client: ApiClient, test_project_id: str) -> str:
    """Create a base topic under the test project for the session."""
    resp = await auth_client.post(
        "/topics/", json={"title": "Autotest-Topic", "project_id": test_project_id}
    )
    resp.raise_for_status()
    topic_id = resp.json()["id"]
    yield topic_id
    await auth_client.delete(f"/topics/{topic_id}")


@pytest_asyncio.fixture(scope="session")
async def test_deliverable_id(auth_client: ApiClient, test_topic_id: str) -> str:
    """Create a base deliverable under the test topic for the session."""
    resp = await auth_client.post(
        "/deliverables/", json={"title": "Autotest-Deliverable", "topic_id": test_topic_id}
    )
    resp.raise_for_status()
    deliverable_id = resp.json()["id"]
    yield deliverable_id
    await auth_client.delete(f"/deliverables/{deliverable_id}")


@pytest_asyncio.fixture
async def cleanup_ids(auth_client: ApiClient):
    """Per-test cleanup registry. Deletes all registered entities after the test."""
    registry = CleanupRegistry()
    yield registry
    await registry.cleanup(auth_client)
