"""F-store (R-010)."""

import httpx

from conftest import (
    EMBED,
    PLAIN,
    RECURSIVE,
    artifact,
    assert_valid,
    new_collection,
    run_stage,
    upload,
)


def _chunked(api: httpx.Client, coll: dict) -> str:  # type: ignore[type-arg]
    f = upload(api, "handbook.md")["files"][0]
    rid = api.post("/ingest-runs", json={"file_id": f["id"], "collection_id": coll["id"]}).json()["id"]
    run_stage(api, "ingest", rid, "parse", PLAIN)
    run_stage(api, "ingest", rid, "chunk", {**RECURSIVE, "length": 100, "overlap": 10})
    return rid


def test_store_writes_and_restore_replaces(api: httpx.Client) -> None:
    coll = new_collection(api, dense="all-minilm")
    rid = _chunked(api, coll)
    emb = artifact(api, run_stage(api, "ingest", rid, "embed", EMBED))
    sr = run_stage(api, "ingest", rid, "store", {})
    assert sr["status"] == "done", sr
    art = artifact(api, sr)
    assert_valid(art, "artifacts/store.schema.json")
    assert art["points_written"] == len(emb["chunks"]) and art["points_deleted"] == 0
    assert art["vector_config"]["dense_name"] == "text-dense" and art["vector_config"]["sparse_name"] == "text-sparse"
    info = api.get(f"/collections/{coll['id']}/qdrant").json()
    assert info["exists"] is True and info["points_count"] == len(emb["chunks"])
    assert info["dense"] == {"name": "text-dense", "size": 384, "distance": "Cosine"}
    assert {"key": "meta.file_id", "type": "keyword"}.items() <= next(i for i in info["payload_indexes"] if i["key"] == "meta.file_id").items()
    again = artifact(api, run_stage(api, "ingest", rid, "store", {}))
    assert again["points_deleted"] == len(emb["chunks"])
    assert api.get(f"/collections/{coll['id']}/qdrant").json()["points_count"] == len(emb["chunks"])
    assert_valid(again["payload_sample"], "qdrant/payload.schema.json")
