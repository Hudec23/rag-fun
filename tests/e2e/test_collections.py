"""F-collections (R-012)."""

import httpx

from conftest import unique


def test_create_list_delete(api: httpx.Client) -> None:
    name = unique("exp")
    r = api.post("/collections", json={"name": name, "dense_model": "nomic-embed-text", "sparse_model": "prithivida/Splade_PP_en_v1"})
    assert r.status_code == 201
    c = r.json()
    assert c["dense_dims"] == 768
    assert c["qdrant_name"] == "rf_" + c["id"].replace("-", "")
    names = [x["name"] for x in api.get("/collections").json()["items"]]
    assert name in names and names == sorted(names)
    dup = api.post("/collections", json={"name": name, "dense_model": "bge-m3", "sparse_model": "Qdrant/bm25"})
    assert dup.status_code == 409 and dup.json()["error"]["code"] == "COLLECTION_NAME_TAKEN"
    assert api.delete(f"/collections/{c['id']}").status_code == 204
    gone = api.get(f"/collections/{c['id']}")
    assert gone.status_code == 404 and gone.json()["error"]["code"] == "COLLECTION_NOT_FOUND"


def test_invalid_collection_body(api: httpx.Client) -> None:
    r = api.post("/collections", json={"name": "Bad Name", "dense_model": "bge-m3", "sparse_model": "Qdrant/bm25"})
    assert r.status_code == 422 and r.json()["error"]["details"]["field"] == "name"
    r = api.post("/collections", json={"name": unique("x"), "dense_model": "gpt", "sparse_model": "Qdrant/bm25"})
    assert r.status_code == 422
