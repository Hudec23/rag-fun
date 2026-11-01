"""F-one-command (R-025): the api bootstraps itself — migrations, buckets, settings, default collection."""

import httpx


def test_default_collection_exists(api: httpx.Client) -> None:
    items = api.get("/collections").json()["items"]
    default = [c for c in items if c["name"] == "default"]
    assert default, items
    assert default[0]["dense_model"] == "bge-m3"
    assert default[0]["sparse_model"] == "Qdrant/bm25"


def test_default_settings(api: httpx.Client) -> None:
    r = api.get("/settings")
    assert r.status_code == 200
    s = r.json()
    assert s["chat_provider"] in ("ollama", "anthropic", "openai_compatible")
    assert s["ollama"]["url"].startswith("http://")
    assert s["ollama"]["chat_model"]
    assert s["reranker_model"] == "Xenova/ms-marco-MiniLM-L-6-v2" or s["reranker_model"] == "BAAI/bge-reranker-base"


def test_buckets_exist(api: httpx.Client) -> None:
    comps = {c["name"]: c for c in api.get("/status").json()["components"]}
    assert comps["s3"]["ok"] is True, comps["s3"]
