"""F-tags (R-003): file + batch tags, normalised, end up in the Qdrant payload."""

import httpx

from conftest import ingest_file, new_collection, upload


def test_patch_tags_normalises(api: httpx.Client) -> None:
    out = upload(api, "notes.txt")
    fid, bid = out["files"][0]["id"], out["batch"]["id"]
    r = api.patch(f"/files/{fid}", json={"tags": ["tax", "2026", "tax"]})
    assert r.status_code == 200
    assert r.json()["tags"] == ["2026", "tax"]
    r = api.patch(f"/batches/{bid}", json={"tags": ["notes"]})
    assert r.status_code == 200 and r.json()["tags"] == ["notes"]
    assert api.patch(f"/files/{fid}", json={"tags": ["UPPER"]}).status_code == 422
    assert api.get("/files", params={"tag": "tax", "batch_id": bid}).json()["page"]["total"] == 1


def test_tags_reach_qdrant_payload(api: httpx.Client) -> None:
    coll = new_collection(api)
    res = ingest_file(api, "notes.txt", coll, tags="meeting")
    fid = res["file"]["id"]
    api.patch(f"/files/{fid}", json={"tags": ["tax"]})
    # re-run store so the new file tags propagate
    r = api.post(f"/ingest-runs/{res['run']['id']}/stages/store", json={"params": {}})
    assert r.status_code == 202
    from conftest import wait_stage

    assert wait_stage(api, r.json()["id"])["status"] == "done"
    pts = api.post(f"/collections/{coll['id']}/qdrant/scroll",
                   json={"filter": {}, "limit": 100, "offset": None, "with_vectors": False}).json()["points"]
    assert pts and all(p["payload"]["meta"]["tags"] == ["meeting", "tax"] for p in pts)
