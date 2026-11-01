"""Example integration test file — house style: `client` (app + postgres-test + fakes),
factories from tests.conftest, exact asserts on status and body."""

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import add_collection


async def test_get_collection_returns_row(
    client: httpx.AsyncClient, session: AsyncSession, frozen_now: object
) -> None:
    row = await add_collection(session, "default")
    await session.commit()
    r = await client.get(f"/api/v1/collections/{row.id}")
    assert r.status_code == 200
    assert r.json() == {
        "id": row.id,
        "name": "default",
        "qdrant_name": "rf_" + row.id.replace("-", ""),
        "dense_model": "bge-m3",
        "dense_dims": 1024,
        "sparse_model": "Qdrant/bm25",
        "created_at": "2026-11-01T18:22:05.123Z",
    }


async def test_get_unknown_collection_is_404(client: httpx.AsyncClient) -> None:
    missing = "019a4b2c-1d00-7b00-8000-0000000000aa"
    r = await client.get(f"/api/v1/collections/{missing}")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "COLLECTION_NOT_FOUND"
    assert r.json()["error"]["details"] == {"collection_id": missing}


async def test_list_collections_sorted_by_name(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    await add_collection(session, "zeta")
    await add_collection(session, "alpha")
    await session.commit()
    r = await client.get("/api/v1/collections")
    assert r.status_code == 200
    assert [c["name"] for c in r.json()["items"]] == ["alpha", "zeta"]


async def test_malformed_collection_id_is_422(client: httpx.AsyncClient) -> None:
    r = await client.get("/api/v1/collections/not-a-uuid")
    assert r.status_code == 422
    assert r.json()["error"]["details"] == {"field": "collection_id"}
