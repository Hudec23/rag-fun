"""F-transform (R-015)."""

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


def test_transform_strategies(api: httpx.Client, coll: dict) -> None:  # type: ignore[type-arg]
    q = "How many vacation days do employees get?"
    none = artifact(api, run_stage(api, "query", _q(api, coll, q), "transform", {"strategy": "none", "num_queries": 3}))
    assert none["queries"] == [q] and none["messages"] == [] and none["model"] is None
    mq = artifact(api, run_stage(api, "query", _q(api, coll, q), "transform", {"strategy": "multi_query", "num_queries": 3}))
    assert_valid(mq, "artifacts/transform.schema.json")
    assert mq["queries"][0] == q and len(mq["queries"]) >= 2 and mq["messages"][0]["role"] == "system"
    hy = artifact(api, run_stage(api, "query", _q(api, coll, q), "transform", {"strategy": "hyde", "num_queries": 3}))
    assert hy["hyde_document"] and hy["queries"] == [hy["hyde_document"]]
