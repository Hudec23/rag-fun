"""Connection probes (R-021): GET the provider's model-list endpoint and never raise."""

import time

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.schemas.settings import TestConnectionRequest, TestConnectionResult
from rag_api.services import app_settings

TIMEOUT = 10


def _latency_ms(start: float) -> int:
    return int(round((time.perf_counter() - start) * 1000))


def _fail(body: TestConnectionRequest, detail: str, latency_ms: int) -> TestConnectionResult:
    return TestConnectionResult(
        target=body.target, ok=False, latency_ms=latency_ms, detail=detail, models=[]
    )


async def test_connection(
    session: AsyncSession, http: httpx.AsyncClient, body: TestConnectionRequest
) -> TestConnectionResult:
    """Never raises for provider problems; timeout 10 s. Values: override fields when given
    (api_key None -> stored key), else stored settings.
    ollama: GET {url}/api/tags -> models = [m['name'] for m in models].
    anthropic: GET https://api.anthropic.com/v1/models, headers x-api-key + anthropic-version
    '2023-06-01' -> models = [d['id'] for d in data].
    openai_compatible: GET {base_url}/models, Authorization 'Bearer <key>' if key -> data[].id.
    Non-2xx -> ok False, detail 'HTTP <status>'; network error -> ok False, detail = str(exc)[:500];
    missing key/base_url -> ok False, detail 'not configured', latency 0."""
    value = await app_settings.load_value(session)
    ov = body.override
    headers: dict[str, str] = {}
    if body.target == "anthropic":
        key = ov.api_key if ov is not None and ov.api_key else value["anthropic"]["api_key"]
        if key is None:
            return _fail(body, "not configured", 0)
        url = "https://api.anthropic.com/v1/models"
        headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    elif body.target == "openai_compatible":
        stored = value["openai_compatible"]
        base_url = ov.base_url if ov is not None and ov.base_url else stored["base_url"]
        if base_url is None:
            return _fail(body, "not configured", 0)
        key = ov.api_key if ov is not None and ov.api_key else stored["api_key"]
        url = base_url + "/models"
        headers = {"Authorization": f"Bearer {key}"} if key else {}
    else:
        url = ov.base_url if ov is not None and ov.base_url else value["ollama"]["url"]
        url = url + "/api/tags"

    start = time.perf_counter()
    try:
        resp = await http.get(url, headers=headers, timeout=TIMEOUT)
    except httpx.HTTPError as exc:
        return _fail(body, str(exc)[:500], _latency_ms(start))
    latency_ms = _latency_ms(start)
    if not 200 <= resp.status_code < 300:
        return _fail(body, f"HTTP {resp.status_code}", latency_ms)
    data = resp.json()
    if body.target == "ollama":
        models = [m["name"] for m in data["models"]]
    else:
        models = [d["id"] for d in data["data"]]
    return TestConnectionResult(
        target=body.target, ok=True, latency_ms=latency_ms, detail=None, models=models
    )
