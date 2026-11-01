"""REST callbacks to the api (contracts/openapi/internal.yaml)."""

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
        raise NotImplementedError("not implemented")

    async def stage_result(self, result: dict[str, Any]) -> None:
        """POST /internal/v1/stage-results with the StageResult body."""
        raise NotImplementedError("not implemented")

    async def put_graph(self, graph: dict[str, Any]) -> None:
        """PUT /internal/v1/pipeline-graphs/{graph['stage']}/{graph['variant']}."""
        raise NotImplementedError("not implemented")
