"""F-generate (R-018), incl. query run-all."""

import httpx

from conftest import (
    artifact,
    assert_valid,
    run_stage,
    wait_stage,
)

RETRIEVE = {"mode": "hybrid", "top_k": 5, "rrf_k": 60, "filters": {}}


def _q(api: httpx.Client, coll: dict, question: str) -> str:  # type: ignore[type-arg]
    r = api.post("/query-runs", json={"collection_id": coll["id"], "question": question})
    assert r.status_code == 201
    return r.json()["id"]


def test_generate_answer_with_citations(api: httpx.Client, coll: dict) -> None:  # type: ignore[type-arg]
    rid = _q(api, coll, "How many vacation days?")
    run_stage(api, "query", rid, "retrieve", RETRIEVE)
    run_stage(api, "query", rid, "rerank", {"enabled": True, "top_n": 3})
    sr = run_stage(api, "query", rid, "generate", {"max_context_tokens": 4000, "temperature": 0.2, "max_answer_tokens": 200})
    assert sr["status"] == "done", sr
    art = artifact(api, sr)
    assert_valid(art, "artifacts/generate.schema.json")
    assert art["answer"].startswith("Fake answer to:") and art["citations"] == [1]
    assert art["context"][0]["n"] == 1 and len(art["context"]) == 3
    b = art["budget"]
    assert b["system_tokens"] + b["question_tokens"] + b["used_context_tokens"] <= b["max_context_tokens"] + b["system_tokens"] + b["question_tokens"]
    assert "Context:" in art["messages"][-1]["content"]
    tiny = run_stage(api, "query", rid, "generate", {"max_context_tokens": 256, "temperature": 0.2, "max_answer_tokens": 50})
    assert artifact(api, tiny)["budget"]["used_context_tokens"] <= 256


def test_query_run_all(api: httpx.Client, coll: dict) -> None:  # type: ignore[type-arg]
    rid = _q(api, coll, "remote work policy")
    params = {"transform": {"strategy": "rewrite", "num_queries": 3}, "retrieve": RETRIEVE,
              "rerank": {"enabled": True, "top_n": 3},
              "generate": {"max_context_tokens": 2000, "temperature": 0.2, "max_answer_tokens": 100}}
    r = api.post(f"/query-runs/{rid}/run-all", json={"from_stage": None, "params": params})
    assert r.status_code == 202
    import time

    for _ in range(240):
        run = api.get(f"/query-runs/{rid}").json()
        if run["stages"]["generate"] and run["stages"]["generate"]["status"] in ("done", "failed"):
            break
        time.sleep(1)
    assert all(run["stages"][s]["status"] == "done" for s in ("transform", "retrieve", "rerank", "generate")), run
    _ = wait_stage
