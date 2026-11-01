"""F-retrieve (R-016)."""

import httpx

from conftest import (
    artifact,
    assert_valid,
    run_stage,
)

RETRIEVE = {"mode": "hybrid", "top_k": 5, "rrf_k": 60, "filters": {}}


def _q(api: httpx.Client, coll: dict, question: str) -> str:  # type: ignore[type-arg]
    r = api.post("/query-runs", json={"collection_id": coll["id"], "question": question})
    assert r.status_code == 201
    return r.json()["id"]


def test_hybrid_retrieval_and_filters(api: httpx.Client, coll: dict) -> None:  # type: ignore[type-arg]
    rid = _q(api, coll, "vacation days per year")
    art = artifact(api, run_stage(api, "query", rid, "retrieve", RETRIEVE))
    assert_valid(art, "artifacts/retrieve.schema.json")
    pq = art["per_query"][0]
    assert pq["query"] == "vacation days per year" and pq["dense"] and pq["sparse"]
    assert "vacation" in art["fused"][0]["hit"]["content"].lower()
    assert art["fused"][0]["source_ranks"]
    tax = {**RETRIEVE, "filters": {"must": [{"key": "tags", "match": {"any": ["tax"]}}]}}
    art2 = artifact(api, run_stage(api, "query", rid, "retrieve", tax))
    assert art2["fused"] and all(f["hit"]["meta"]["tags"] == ["tax"] for f in art2["fused"])
    dense = artifact(api, run_stage(api, "query", rid, "retrieve", {**RETRIEVE, "mode": "dense"}))
    assert dense["per_query"][0]["sparse"] is None
