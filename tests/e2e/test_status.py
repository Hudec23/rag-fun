"""F-status (R-024)."""

import httpx

from conftest import assert_valid

ORDER = ["api", "worker-ingest", "worker-query", "postgres", "redis", "qdrant", "s3", "ollama"]


def test_status_reports_every_component(api: httpx.Client) -> None:
    r = api.get("/status")
    assert r.status_code == 200
    comps = r.json()["components"]
    assert [c["name"] for c in comps] == ORDER
    ok = {c["name"]: c["ok"] for c in comps}
    for name in ORDER[:-1]:
        assert ok[name] is True, comps
    ollama = comps[-1]
    assert ollama["ok"] is False and ollama["detail"]  # no Ollama in the e2e stack
    assert all(isinstance(c["latency_ms"], int) and c["latency_ms"] >= 0 for c in comps)


def test_model_catalog_without_ollama(api: httpx.Client) -> None:
    cat = api.get("/models").json()
    assert cat["ollama_reachable"] is False
    assert [d["model"] for d in cat["dense"]] == ["bge-m3", "nomic-embed-text", "mxbai-embed-large", "all-minilm"]
    assert all(d["installed"] is False for d in cat["dense"])
    assert cat["sparse"] == ["Qdrant/bm25", "prithivida/Splade_PP_en_v1"]
    assert_valid(cat["dense"][0]["dims"], "shared/common.schema.json#/$defs/DenseModelConfig/properties/dims")
