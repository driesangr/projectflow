"""Cleanup registry for test isolation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils.api_client import ApiClient


# Maps artifact type to its DELETE endpoint prefix
_ENDPOINT_MAP: dict[str, str] = {
    "task": "/tasks",
    "user_story": "/user-stories",
    "deliverable": "/deliverables",
    "topic": "/topics",
    "project": "/projects",
    "users": "/users",
}


@dataclass
class CleanupRegistry:
    """Collect IDs to delete after a test."""

    _entries: list[tuple[str, str]] = field(default_factory=list)

    def add(self, artifact_type: str, entity_id: str) -> None:
        """Register an entity for deletion."""
        if artifact_type not in _ENDPOINT_MAP:
            raise ValueError(f"Unknown artifact type: {artifact_type!r}")
        self._entries.append((artifact_type, entity_id))

    async def cleanup(self, client: "ApiClient") -> None:
        """Delete all registered entities (in reverse registration order)."""
        for artifact_type, entity_id in reversed(self._entries):
            endpoint = f"{_ENDPOINT_MAP[artifact_type]}/{entity_id}"
            try:
                await client.delete(endpoint)
            except Exception:
                pass  # Best-effort cleanup
        self._entries.clear()
