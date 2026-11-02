"""Integration tests for rag_api.services.connection_test: test_connection probes.
Real postgres via the `session` fixture; outbound HTTP is mocked with respx so no
real sockets are opened. The service is still a stub — every test here is red until
T-api-022."""

import httpx
import respx
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.schemas.settings import ConnectionOverride, TestConnectionRequest
from rag_api.services import connection_test
from tests.conftest import add_settings

ANTHROPIC_KEY = "sk-ant-secret-abcd"
ANTHROPIC_MODEL = "claude-sonnet-5-5"
ANTHROPIC_MODELS_URL = "https://api.anthropic.com/v1/models"
OLLAMA_MODEL = "qwen3:8b"
OLLAMA_TAGS_URL = "http://ollama-fake:11434/api/tags"
OPENAI_BASE_URL = "http://lm:1234/v1"
OPENAI_KEY = "k"
OPENAI_MODEL = "gpt-fake"
RERANKER_MODEL = "Xenova/ms-marco-MiniLM-L-6-v2"

ANTHROPIC_VALUE = {
    "chat_provider": "anthropic",
    "ollama": {"url": "http://ollama-fake:11434", "chat_model": OLLAMA_MODEL},
    "anthropic": {"model": ANTHROPIC_MODEL, "api_key": ANTHROPIC_KEY},
    "openai_compatible": {"base_url": None, "model": None, "api_key": None},
    "reranker_model": RERANKER_MODEL,
}


async def test_ollama_success(session: AsyncSession) -> None:
    await add_settings(session)

    async with respx.mock() as mock:
        route = mock.get(OLLAMA_TAGS_URL).respond(json={"models": [{"name": OLLAMA_MODEL}]})
        async with httpx.AsyncClient() as http:
            result = await connection_test.test_connection(
                session, http, TestConnectionRequest(target="ollama")
            )

    assert result.ok is True
    assert result.models == [OLLAMA_MODEL]
    assert result.latency_ms >= 0
    assert str(route.calls.last.request.url) == OLLAMA_TAGS_URL


async def test_ollama_connect_error(session: AsyncSession) -> None:
    await add_settings(session)

    async with respx.mock() as mock:
        mock.get(OLLAMA_TAGS_URL).mock(side_effect=httpx.ConnectError("x"))
        async with httpx.AsyncClient() as http:
            result = await connection_test.test_connection(
                session, http, TestConnectionRequest(target="ollama")
            )

    assert result.ok is False
    assert result.detail is not None
    assert "x" in result.detail
    assert result.models == []


async def test_anthropic_with_stored_key(session: AsyncSession) -> None:
    await add_settings(session, value=ANTHROPIC_VALUE)

    async with respx.mock() as mock:
        route = mock.get(ANTHROPIC_MODELS_URL).respond(json={"data": [{"id": ANTHROPIC_MODEL}]})
        async with httpx.AsyncClient() as http:
            result = await connection_test.test_connection(
                session, http, TestConnectionRequest(target="anthropic")
            )

    assert result.ok is True
    assert result.models == [ANTHROPIC_MODEL]
    assert str(route.calls.last.request.url) == ANTHROPIC_MODELS_URL
    assert route.calls.last.request.headers["x-api-key"] == ANTHROPIC_KEY
    assert route.calls.last.request.headers["anthropic-version"] == "2023-06-01"


async def test_anthropic_without_key(session: AsyncSession) -> None:
    await add_settings(session)

    async with respx.mock() as mock:
        async with httpx.AsyncClient() as http:
            result = await connection_test.test_connection(
                session, http, TestConnectionRequest(target="anthropic")
            )

    assert result.ok is False
    assert result.detail == "not configured"
    assert result.latency_ms == 0
    assert result.models == []
    assert len(mock.calls) == 0


async def test_openai_compatible_override(session: AsyncSession) -> None:
    await add_settings(session)
    body = TestConnectionRequest(
        target="openai_compatible",
        override=ConnectionOverride(base_url=OPENAI_BASE_URL, api_key=OPENAI_KEY),
    )

    async with respx.mock() as mock:
        route = mock.get(OPENAI_BASE_URL + "/models").respond(json={"data": [{"id": OPENAI_MODEL}]})
        async with httpx.AsyncClient() as http:
            result = await connection_test.test_connection(session, http, body)

    assert result.ok is True
    assert result.models == [OPENAI_MODEL]
    assert str(route.calls.last.request.url) == OPENAI_BASE_URL + "/models"
    assert route.calls.last.request.headers["authorization"] == f"Bearer {OPENAI_KEY}"


async def test_http_401(session: AsyncSession) -> None:
    await add_settings(session)

    async with respx.mock() as mock:
        mock.get(OLLAMA_TAGS_URL).respond(401)
        async with httpx.AsyncClient() as http:
            result = await connection_test.test_connection(
                session, http, TestConnectionRequest(target="ollama")
            )

    assert result.ok is False
    assert result.detail == "HTTP 401"
    assert result.models == []
