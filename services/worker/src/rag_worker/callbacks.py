"""REST callbacks to the api (contracts/openapi/internal.yaml)."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

RETRY_DELAYS = [1, 2, 4, 8, 16]  # seconds between the 5 attempts' failures


class ApiClient:
    """POST/PUT with header X-Internal-Token. Retry on httpx.TransportError or 5xx: up to 5 attempts
    total, sleeping RETRY_DELAYS[i] after failed attempt i (no sleep after the last). 4xx: no retry,
    raise httpx.HTTPStatusError. After the last failed attempt re-raise the last error."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        token: str,
        sleep: Callable[[float], Awaitable[None]] | None = None,
    ) -> None:
        self.http = http
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.sleep = sleep  # None -> asyncio.sleep; tests pass a recorder

    async def stage_started(self, stage_run_id: str, started_at: str) -> None:
        """POST /internal/v1/stage-started {stage_run_id, started_at}."""
        await self._request(
            "POST",
            f"{self.base_url}/internal/v1/stage-started",
            {"stage_run_id": stage_run_id, "started_at": started_at},
        )

    async def stage_result(self, result: dict[str, Any]) -> None:
        """POST /internal/v1/stage-results with the StageResult body."""
        await self._request("POST", f"{self.base_url}/internal/v1/stage-results", result)

    async def put_graph(self, graph: dict[str, Any]) -> None:
        """PUT /internal/v1/pipeline-graphs/{graph['stage']}/{graph['variant']}."""
        await self._request(
            "PUT",
            f"{self.base_url}/internal/v1/pipeline-graphs/{graph['stage']}/{graph['variant']}",
            graph,
        )

    async def _request(self, method: str, url: str, body: dict[str, Any]) -> None:
        """Send with header X-Internal-Token; retry on TransportError/5xx up to len(RETRY_DELAYS)
        attempts, sleeping RETRY_DELAYS[i] after failed attempt i (none after the last). 4xx raises
        immediately; after the last failed attempt the last error is re-raised."""
        last_error: BaseException | None = None
        for attempt in range(len(RETRY_DELAYS)):
            try:
                response = await self.http.request(
                    method,
                    url,
                    json=body,
                    headers={"X-Internal-Token": self.token},
                )
                response.raise_for_status()
                return
            except httpx.TransportError as e:
                last_error = e
            except httpx.HTTPStatusError as e:
                if e.response.status_code < 500:
                    raise
                last_error = e
            if attempt + 1 < len(RETRY_DELAYS):
                await self._sleep(RETRY_DELAYS[attempt])
        assert last_error is not None
        raise last_error

    async def _sleep(self, seconds: float) -> None:
        if self.sleep is None:
            await asyncio.sleep(seconds)
        else:
            await self.sleep(seconds)
