"""Integration tests for GET /api/v1/models (rag_api.services.models_catalog.get_catalog).
Real postgres via the `client`/`session` fixtures; outbound HTTP (ollama) is mocked
with respx so no real sockets are opened. The service is still a stub — every test
here is red until T-api-024."""

import httpx
import respx
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import add_settings

OLLAMA_TAGS_URL = "http://ollama-fake:11434/api/tags"


async def test_installed_from_ollama_tags(client: httpx.AsyncClient, session: AsyncSession) -> None:
    await add_settings(session)
    await session.commit()

    async with respx.mock() as mock:
        route = mock.get(OLLAMA_TAGS_URL).respond(
            json={"models": [{"name": "bge-m3:latest"}, {"name": "qwen3:8b"}]}
        )
        r = await client.get("/api/v1/models")

    assert r.status_code == 200
    body = r.json()
    assert str(route.calls.last.request.url) == OLLAMA_TAGS_URL
    assert body["ollama_reachable"] is True
    assert body["ollama_installed"] == ["bge-m3:latest", "qwen3:8b"]
    assert body["dense"] == [
        {"model": "bge-m3", "dims": 1024, "max_tokens": 8192, "installed": True},
        {"model": "nomic-embed-text", "dims": 768, "max_tokens": 8192, "installed": False},
        {"model": "mxbai-embed-large", "dims": 1024, "max_tokens": 512, "installed": False},
        {"model": "all-minilm", "dims": 384, "max_tokens": 256, "installed": False},
    ]


async def test_bare_tag_counts_as_installed(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    await add_settings(session)
    await session.commit()

    async with respx.mock() as mock:
        mock.get(OLLAMA_TAGS_URL).respond(json={"models": [{"name": "all-minilm"}]})
        r = await client.get("/api/v1/models")

    assert r.status_code == 200
    body = r.json()
    assert body["ollama_reachable"] is True
    assert body["ollama_installed"] == ["all-minilm"]
    by_model = {entry["model"]: entry for entry in body["dense"]}
    assert by_model["all-minilm"]["installed"] is True
    for name in ("bge-m3", "nomic-embed-text", "mxbai-embed-large"):
        assert by_model[name]["installed"] is False


async def test_non_matching_tag_not_installed(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    await add_settings(session)
    await session.commit()

    async with respx.mock() as mock:
        mock.get(OLLAMA_TAGS_URL).respond(json={"models": [{"name": "bge-m3x:latest"}]})
        r = await client.get("/api/v1/models")

    assert r.status_code == 200
    body = r.json()
    assert body["ollama_reachable"] is True
    assert body["ollama_installed"] == ["bge-m3x:latest"]
    by_model = {entry["model"]: entry for entry in body["dense"]}
    assert by_model["bge-m3"]["installed"] is False
    for name in ("nomic-embed-text", "mxbai-embed-large", "all-minilm"):
        assert by_model[name]["installed"] is False


async def test_ollama_down_not_reachable(client: httpx.AsyncClient, session: AsyncSession) -> None:
    await add_settings(session)
    await session.commit()

    async with respx.mock() as mock:
        mock.get(OLLAMA_TAGS_URL).mock(side_effect=httpx.ConnectError("ollama down"))
        r = await client.get("/api/v1/models")

    assert r.status_code == 200
    body = r.json()
    assert body["ollama_reachable"] is False
    assert body["ollama_installed"] == []
    for entry in body["dense"]:
        assert entry["installed"] is False
    assert [entry["model"] for entry in body["dense"]] == [
        "bge-m3",
        "nomic-embed-text",
        "mxbai-embed-large",
        "all-minilm",
    ]


async def test_sparse_and_rerank_from_catalog(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    await add_settings(session)
    await session.commit()

    async with respx.mock() as mock:
        mock.get(OLLAMA_TAGS_URL).respond(json={"models": []})
        r = await client.get("/api/v1/models")

    assert r.status_code == 200
    body = r.json()
    assert body["sparse"] == ["Qdrant/bm25", "prithivida/Splade_PP_en_v1"]
    assert body["rerank"] == ["Xenova/ms-marco-MiniLM-L-6-v2", "BAAI/bge-reranker-base"]
