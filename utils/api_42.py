import asyncio
import time
from typing import Any

import httpx

from utils import print_error, print_log

CAMPUS_ID = 62
CURSUS_ID = 9


class FourtyTwoAPI:
    BASE_URL = "https://api.intra.42.fr/v2"

    def __init__(self, uid: str, secret: str) -> None:
        self.uid = uid
        self.secret = secret
        self._token: str | None = None
        self._token_expires_at: float = 0
        self._client = httpx.AsyncClient(timeout=30.0)
        self._lock = asyncio.Lock()
        self._call_count: int = 0

    async def close(self) -> None:
        await self._client.aclose()

    def get_and_reset_call_count(self) -> int:
        count = self._call_count
        self._call_count = 0
        return count

    async def _get_token(self) -> str:
        async with self._lock:
            if self._token and time.time() < self._token_expires_at:
                return self._token

            print_log("Requesting new 42 API token...")
            resp = await self._client.post(
                "https://api.intra.42.fr/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.uid,
                    "client_secret": self.secret,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            self._token = data["access_token"]
            self._token_expires_at = time.time() + data["expires_in"] - 300
            print_log("42 API token obtained.")
            return self._token

    async def _request(
        self, method: str, path: str, retries: int = 3, **kwargs: Any
    ) -> Any:
        for attempt in range(retries):
            token = await self._get_token()
            headers = {"Authorization": f"Bearer {token}"}

            resp = await self._client.request(
                method, f"{self.BASE_URL}{path}", headers=headers, **kwargs
            )
            self._call_count += 1

            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", 2))
                print_log(f"42 API rate limited, retrying in {retry_after}s...")
                await asyncio.sleep(retry_after)
                continue

            resp.raise_for_status()
            return resp.json()

        print_error(f"42 API request failed after {retries} retries: {path}")
        return None

    async def _request_all(self, path: str, **kwargs: Any) -> list[dict]:
        items: list[dict] = []
        page = 1
        while True:
            sep = "&" if "?" in path else "?"
            data = await self._request(
                "GET",
                f"{path}{sep}page[size]=100&page[number]={page}",
                **kwargs,
            )
            if not data or not isinstance(data, list) or len(data) == 0:
                break
            items.extend(data)
            if len(data) < 100:
                break
            page += 1
            await asyncio.sleep(0.1)
        return items

    async def get_user(self, login: str) -> dict | None:
        return await self._request("GET", f"/users/{login}")

    async def get_user_projects(self, login: str) -> list[dict]:
        return await self._request_all(f"/users/{login}/projects_users")

    async def get_user_locations(self, login: str) -> list[dict]:
        return await self._request_all(f"/users/{login}/locations")

    async def get_user_evaluations(self, login: str) -> list[dict]:
        return await self._request_all(f"/users/{login}/evaluations")
