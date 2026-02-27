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


@pytest_asyncio.fixture
async def cleanup_ids(auth_client: ApiClient):
    """Per-test cleanup registry. Deletes all registered entities after the test."""
    registry = CleanupRegistry()
    yield registry
    await registry.cleanup(auth_client)
