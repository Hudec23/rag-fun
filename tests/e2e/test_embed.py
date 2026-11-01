"""F-embed (R-008, R-009)."""

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


def test_embed_is_inspectable_before_store(api: httpx.Client) -> None:
    coll = new_collection(api, dense="all-minilm")
    rid = _chunked(api, coll)
    sr = run_stage(api, "ingest", rid, "embed", EMBED)
    assert sr["status"] == "done", sr
    art = artifact(api, sr)
    assert_valid(art, "artifacts/embed.schema.json")
    n = len(art["chunks"])
    assert n >= 5 and art["dense_dims"] == 384
    assert all(len(c["dense"]) == 384 and c["sparse"]["indices"] for c in art["chunks"])
    assert all(c["tokens"][0] == "[CLS]" and c["token_count"] >= len(c["tokens"]) - 0 for c in art["chunks"])
    assert len(art["similarity"]) == n and all(abs(art["similarity"][i][i] - 1) < 1e-6 for i in range(n))
    assert len(art["projections"]["pca2"]) == n and art["projections"]["umap2"] is not None
    info = api.get(f"/collections/{coll['id']}/qdrant").json()
    assert info["exists"] is False or info["points_count"] == 0
