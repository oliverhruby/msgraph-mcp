"""Microsoft Graph HTTP client with retry, throttle, pagination, and batching."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger("msgraph_mcp.client")

MAX_PAGES = int(os.getenv("MSGRAPH_MAX_PAGES", "50"))
API_VERSION = os.getenv("MSGRAPH_API_VERSION", "v1.0")
REQUEST_TIMEOUT = float(os.getenv("MSGRAPH_TIMEOUT", "30"))


class GraphError(Exception):
    def __init__(self, status: int, body: Any, url: str):
        self.status = status
        self.body = body
        self.url = url
        msg = body.get("error", {}).get("message", str(body)) if isinstance(body, dict) else str(body)
        super().__init__(f"Graph {status} {url}: {msg}")


class GraphClient:
    """Async httpx client for Microsoft Graph with automatic token injection."""

    def __init__(self, auth):
        from .auth import AuthManager
        self._auth: AuthManager = auth
        self._http = httpx.AsyncClient(
            base_url=f"{auth.base_url}/{API_VERSION}",
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        )

    async def _headers(self) -> dict:
        token = self._auth.acquire_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        content: Any = None,
        params: dict | None = None,
        headers: dict | None = None,
        beta: bool = False,
    ) -> Any:
        """Make a Graph API request with retry and throttle handling."""
        url = self._build_url(path, beta)
        hdrs = await self._headers()
        if headers:
            hdrs.update(headers)

        last_error = None
        for attempt in range(4):
            try:
                if content is not None:
                    resp = await self._http.request(
                        method, url, content=content, params=params, headers=hdrs,
                    )
                else:
                    resp = await self._http.request(
                        method, url, json=json, params=params, headers=hdrs,
                    )
            except httpx.TransportError as e:
                last_error = e
                time.sleep(2 ** attempt)
                continue

            if resp.status_code in (200, 201, 202, 204):
                return resp.json() if resp.content else {}

            if resp.status_code in (429, 503, 504):
                retry_after = int(resp.headers.get("Retry-After", 2 ** (attempt + 1)))
                logger.warning("Throttled (%d), retrying in %ds", resp.status_code, retry_after)
                time.sleep(retry_after)
                continue

            try:
                body = resp.json()
            except Exception:
                body = {"error": {"message": resp.text}}
            raise GraphError(resp.status_code, body, url)

        if last_error:
            raise last_error
        raise GraphError(429, {"error": {"message": "Max retries exceeded"}}, url)

    async def get(self, path: str, *, params: dict | None = None, beta: bool = False) -> Any:
        return await self.request("GET", path, params=params, beta=beta)

    async def post(self, path: str, *, json: Any = None, params: dict | None = None, beta: bool = False) -> Any:
        return await self.request("POST", path, json=json, params=params, beta=beta)

    async def patch(self, path: str, *, json: Any = None, params: dict | None = None, beta: bool = False) -> Any:
        return await self.request("PATCH", path, json=json, params=params, beta=beta)

    async def delete(self, path: str, *, params: dict | None = None, beta: bool = False) -> Any:
        return await self.request("DELETE", path, params=params, beta=beta)

    async def put(self, path: str, *, json: Any = None, content: Any = None, params: dict | None = None, headers: dict | None = None, beta: bool = False) -> Any:
        return await self.request("PUT", path, json=json, content=content, params=params, headers=headers, beta=beta)

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------
    async def get_all(
        self,
        path: str,
        *,
        params: dict | None = None,
        max_pages: int | None = None,
        beta: bool = False,
    ) -> list:
        """Follow @odata.nextLink to collect all pages."""
        pages = max_pages if max_pages is not None else MAX_PAGES
        results = []
        url = self._build_url(path, beta)
        hdrs = await self._headers()
        query_params = dict(params) if params else {}

        for _ in range(pages):
            resp = await self._http.get(url, params=query_params, headers=hdrs)

            if resp.status_code == 200:
                data = resp.json()
            elif resp.status_code in (429, 503, 504):
                retry_after = int(resp.headers.get("Retry-After", 5))
                time.sleep(retry_after)
                continue
            else:
                try:
                    body = resp.json()
                except Exception:
                    body = {"error": {"message": resp.text}}
                raise GraphError(resp.status_code, body, str(url))

            items = data.get("value", [])
            results.extend(items)

            next_link = data.get("@odata.nextLink")
            if not next_link:
                break
            url = next_link
            query_params = {}  # nextLink contains full query

        return results

    # ------------------------------------------------------------------
    # Delta
    # ------------------------------------------------------------------
    async def get_delta(self, path: str, *, delta_token: str | None = None, params: dict | None = None) -> tuple[list, str | None]:
        """Execute a delta query, returns (items, new_delta_token)."""
        if delta_token:
            path = f"{path}/delta"
            params = dict(params or {})
            params["$deltatoken"] = delta_token
        else:
            path = f"{path}/delta"
        data = await self.get(path, params=params)
        items = data.get("value", [])
        new_token = data.get("@odata.deltaLink")
        if new_token and "$deltatoken=" in new_token:
            new_token = new_token.split("$deltatoken=")[-1].split("&")[0]
        elif not data.get("@odata.nextLink"):
            new_token = None
        return items, new_token

    # ------------------------------------------------------------------
    # Batch (up to 20 requests)
    # ------------------------------------------------------------------
    async def batch(self, requests: list[dict]) -> list:
        """Execute up to 20 Graph requests in a single $batch call."""
        if len(requests) > 20:
            raise ValueError("$batch supports a maximum of 20 requests")
        payload = {"requests": requests}
        result = await self.post("/$batch", json=payload)
        return result.get("responses", [])

    # ------------------------------------------------------------------
    # URL building
    # ------------------------------------------------------------------
    def _build_url(self, path: str, beta: bool = False) -> str:
        base = self._auth.base_url
        version = "beta" if beta else API_VERSION
        if path.startswith("http"):
            return path
        return f"{base}/{version}{path}" if not path.startswith("/") else f"{base}/{version}{path}"

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    async def close(self):
        await self._http.aclose()
