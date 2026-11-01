"""F-rerank (R-017)."""

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


def test_rerank_needs_retrieve_then_reorders(api: httpx.Client, coll: dict) -> None:  # type: ignore[type-arg]
    rid = _q(api, coll, "tax refund rules")
    r = api.post(f"/query-runs/{rid}/stages/rerank", json={"params": {"enabled": True, "top_n": 2}})
    assert r.status_code == 409 and r.json()["error"]["details"]["missing"] == "retrieve"
    run_stage(api, "query", rid, "retrieve", RETRIEVE)
    art = artifact(api, run_stage(api, "query", rid, "rerank", {"enabled": True, "top_n": 2}))
    assert_valid(art, "artifacts/rerank.schema.json")
    assert len(art["after"]) == 2 and art["after"][0]["rerank_score"] is not None
    assert "tax refund" in art["after"][0]["hit"]["content"].lower()
    off = artifact(api, run_stage(api, "query", rid, "rerank", {"enabled": False, "top_n": 3}))
    assert [a["hit"]["doc_id"] for a in off["after"]] == [b["doc_id"] for b in off["before"][:3]]
    assert all(a["rerank_score"] is None for a in off["after"])
