"""API client helper for integration tests."""

from __future__ import annotations

import httpx

BASE_URL = "http://localhost:8000"
AUTH_URL = f"{BASE_URL}/auth/login"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}


class ApiClient:
    """Authenticated HTTP client for ProjectFlow API."""

    def __init__(self, token: str) -> None:
        self._token = token
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )

    @classmethod
    async def authenticate(
        cls,
        username: str = ADMIN_CREDENTIALS["username"],
        password: str = ADMIN_CREDENTIALS["password"],
    ) -> "ApiClient":
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                AUTH_URL,
                data={"username": username, "password": password},
            )
            resp.raise_for_status()
            token = resp.json()["access_token"]
        return cls(token)

    async def get(self, path: str, **kwargs) -> httpx.Response:
        return await self._client.get(path, **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        return await self._client.post(path, **kwargs)

    async def put(self, path: str, **kwargs) -> httpx.Response:
        return await self._client.put(path, **kwargs)

    async def patch(self, path: str, **kwargs) -> httpx.Response:
        return await self._client.patch(path, **kwargs)

    async def delete(self, path: str, **kwargs) -> httpx.Response:
        return await self._client.delete(path, **kwargs)

    async def aclose(self) -> None:
        await self._client.aclose()
