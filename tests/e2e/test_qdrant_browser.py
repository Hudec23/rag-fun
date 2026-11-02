"""F-qdrant-browser (R-011)."""

import httpx

from conftest import assert_valid, ingest_file, new_collection


def test_browse_filter_facet_point(api: httpx.Client) -> None:
    coll = new_collection(api)
    hr = ingest_file(api, "handbook.md", coll, tags="hr")
    ingest_file(api, "notes.txt", coll, tags="tax")
    base = f"/collections/{coll['id']}/qdrant"
    flt = {"must": [{"key": "tags", "match": {"any": ["hr"]}}]}
    page = api.post(f"{base}/scroll", json={"filter": flt, "limit": 1, "offset": None, "with_vectors": False}).json()
    assert len(page["points"]) == 1 and page["next_offset"] is not None
    assert all(p["payload"]["meta"]["file_id"] == hr["file"]["id"] and p["vectors"] is None for p in page["points"])
    for p in page["points"]:
        assert_valid(p["payload"], "qdrant/payload.schema.json")
    total = api.post(f"{base}/count", json={"filter": {}}).json()["count"]
    hr_count = api.post(f"{base}/count", json={"filter": flt}).json()["count"]
    assert 0 < hr_count < total
    facet = api.get(f"{base}/facets/tags").json()
    assert {v["value"] for v in facet["values"]} == {"hr", "tax"}
    pid = page["points"][0]["id"]
    point = api.get(f"{base}/points/{pid}").json()
    assert len(point["vectors"]["dense"]) == 384 and point["vectors"]["sparse"]["indices"]
    missing = api.get(f"{base}/points/{'0' * 32}")
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "POINT_NOT_FOUND"
    rng = {"must": [{"key": "page", "range": {"gte": 1}}]}
    assert api.post(f"{base}/count", json={"filter": rng}).status_code == 200


def test_empty_collection_info(api: httpx.Client) -> None:
    coll = new_collection(api)
    info = api.get(f"/collections/{coll['id']}/qdrant").json()
    assert info == {"qdrant_name": coll["qdrant_name"], "exists": False, "status": None, "points_count": None,
                    "dense": None, "sparse": None, "payload_indexes": []}
    sc = api.post(f"/collections/{coll['id']}/qdrant/scroll", json={"filter": {}, "limit": 10, "offset": None, "with_vectors": False})
    assert sc.json() == {"points": [], "next_offset": None}
