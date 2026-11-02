"""Unit tests for rag_worker.callbacks.ApiClient: internal REST callbacks with retries.
Outbound HTTP is mocked with respx and sleep is a recorder, so no sockets and no clocks.
The client is a stub — every test here is red until T-worker-006.
Assertions on mock.calls stay inside the respx.mock() block: respx clears its call history on exit."""

import json

import httpx
import pytest
import respx

from rag_worker.callbacks import ApiClient
from tests.conftest import FIXTURES

BASE_URL = "http://api:8000"
TOKEN = "test-internal-token"
STAGE_STARTED_URL = BASE_URL + "/internal/v1/stage-started"
STAGE_RESULTS_URL = BASE_URL + "/internal/v1/stage-results"
STARTED_AT = "2026-11-01T18:22:05.123Z"
STAGE_RESULT_BODY = {
    "stage_run_id": "019a4b2c-2100-7c00-9000-000000000003",
    "status": "done",
    "artifact_key": "019a4b2c-2000-7c00-9000-000000000002/chunk/v1.json",
    "summary": {
        "stage": "chunk",
        "chunks": 42,
        "min_chars": 120,
        "max_chars": 998,
        "mean_chars": 731.5,
    },
    "error": None,
    "started_at": "2026-11-01T18:22:05.123Z",
    "finished_at": "2026-11-01T18:22:07.456Z",
}
PIPELINE_GRAPH = json.loads((FIXTURES / "shared__pipeline-graph.json").read_text())


def _client(http: httpx.AsyncClient, sleeps: list[float], base_url: str = BASE_URL) -> ApiClient:
    async def recorder(seconds: float) -> None:
        sleeps.append(seconds)

    return ApiClient(http, base_url, TOKEN, sleep=recorder)


async def test_stage_started_posts_to_internal_endpoint() -> None:
    sleeps: list[float] = []

    async with respx.mock() as mock:
        mock.post(STAGE_STARTED_URL).respond(204)
        async with httpx.AsyncClient() as http:
            await _client(http, sleeps).stage_started("id1", STARTED_AT)

        [call] = mock.calls
        assert str(call.request.url) == STAGE_STARTED_URL
        assert call.request.headers["X-Internal-Token"] == TOKEN
        assert json.loads(call.request.content) == {"stage_run_id": "id1", "started_at": STARTED_AT}
        assert sleeps == []


async def test_stage_result_posts_body_unchanged() -> None:
    sleeps: list[float] = []

    async with respx.mock() as mock:
        mock.post(STAGE_RESULTS_URL).respond(204)
        async with httpx.AsyncClient() as http:
            await _client(http, sleeps).stage_result(STAGE_RESULT_BODY)

        [call] = mock.calls
        assert str(call.request.url) == STAGE_RESULTS_URL
        assert call.request.headers["X-Internal-Token"] == TOKEN
        assert json.loads(call.request.content) == STAGE_RESULT_BODY
        assert sleeps == []


async def test_put_graph_puts_graph_to_stage_variant_path() -> None:
    sleeps: list[float] = []
    graph_url = BASE_URL + "/internal/v1/pipeline-graphs/chunk/fixed"

    async with respx.mock() as mock:
        mock.put(graph_url).respond(204)
        async with httpx.AsyncClient() as http:
            await _client(http, sleeps).put_graph(PIPELINE_GRAPH)

        [call] = mock.calls
        assert str(call.request.url) == graph_url
        assert call.request.headers["X-Internal-Token"] == TOKEN
        assert json.loads(call.request.content) == PIPELINE_GRAPH
        assert sleeps == []


async def test_503s_then_204_retries_with_backoff() -> None:
    sleeps: list[float] = []

    async with respx.mock() as mock:
        mock.post(STAGE_STARTED_URL).mock(
            side_effect=[httpx.Response(503), httpx.Response(503), httpx.Response(204)]
        )
        async with httpx.AsyncClient() as http:
            await _client(http, sleeps).stage_started("id1", STARTED_AT)

        assert mock.calls.call_count == 3
        assert mock.calls.last.response.status_code == 204
        assert sleeps == [1, 2]


async def test_five_connect_errors_retried_then_reraised() -> None:
    sleeps: list[float] = []

    async with respx.mock() as mock:
        mock.post(STAGE_STARTED_URL).mock(side_effect=httpx.ConnectError("api unreachable"))
        async with httpx.AsyncClient() as http:
            with pytest.raises(httpx.ConnectError):
                await _client(http, sleeps).stage_started("id1", STARTED_AT)

        assert mock.calls.call_count == 5
        assert sleeps == [1, 2, 4, 8]


async def test_404_raises_http_status_error_without_retry() -> None:
    sleeps: list[float] = []

    async with respx.mock() as mock:
        mock.post(STAGE_STARTED_URL).respond(404)
        async with httpx.AsyncClient() as http:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await _client(http, sleeps).stage_started("id1", STARTED_AT)

        assert exc_info.value.response.status_code == 404
        assert mock.calls.call_count == 1
        assert sleeps == []


async def test_trailing_slash_base_url_builds_single_slash_url() -> None:
    sleeps: list[float] = []

    async with respx.mock() as mock:
        mock.post(STAGE_STARTED_URL).respond(204)
        async with httpx.AsyncClient() as http:
            client = _client(http, sleeps, base_url=BASE_URL + "/")
            await client.stage_started("id1", STARTED_AT)

        [call] = mock.calls
        assert str(call.request.url) == STAGE_STARTED_URL
        assert sleeps == []
