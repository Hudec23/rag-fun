"""F-upload (R-001, R-002)."""

import hashlib

import httpx

from conftest import FIXTURES, upload


def test_multi_upload_stores_every_file(api: httpx.Client) -> None:
    out = upload(api, "handbook.md", "q3-report.pdf", "scan-invoice.png", name="mixed batch", tags="hr, Docs")
    assert out["batch"]["name"] == "mixed batch"
    assert out["batch"]["tags"] == ["docs", "hr"]
    assert out["batch"]["file_count"] == 3
    assert [f["filename"] for f in out["files"]] == ["handbook.md", "q3-report.pdf", "scan-invoice.png"]
    assert [f["mime"] for f in out["files"]] == ["text/markdown", "application/pdf", "image/png"]
    pdf = out["files"][1]
    assert pdf["sha256"] == hashlib.sha256((FIXTURES / "q3-report.pdf").read_bytes()).hexdigest()
    content = api.get(f"/files/{pdf['id']}/content")
    assert content.status_code == 200
    assert content.headers["content-type"] == "application/pdf"
    assert content.content == (FIXTURES / "q3-report.pdf").read_bytes()
    listed = api.get("/files", params={"batch_id": out["batch"]["id"]}).json()
    assert listed["page"]["total"] == 3
    batch = api.get(f"/batches/{out['batch']['id']}").json()
    assert [f["id"] for f in batch["files"]] == [f["id"] for f in out["files"]]


def test_unsupported_type_rejects_whole_batch(api: httpx.Client) -> None:
    before = api.get("/batches", params={"limit": 1}).json()["page"]["total"]
    files = [("files", ("notes.txt", b"ok")), ("files", ("unsupported.rtf", (FIXTURES / "unsupported.rtf").read_bytes()))]
    r = api.post("/batches", files=files)
    assert r.status_code == 415
    assert r.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"
    assert r.json()["error"]["details"] == {"filename": "unsupported.rtf"}
    assert api.get("/batches", params={"limit": 1}).json()["page"]["total"] == before


def test_empty_upload_and_bad_tags(api: httpx.Client) -> None:
    r = api.post("/batches", data={"name": "x"}, files=[])
    assert r.status_code in (400, 422)
    assert r.json()["error"]["code"] in ("EMPTY_UPLOAD", "VALIDATION_ERROR")
    r = api.post("/batches", files=[("files", ("a.txt", b"a"))], data={"tags": "ok,Bad Tag!"})
    assert r.status_code == 422
    assert r.json()["error"]["details"]["field"] == "tags"
