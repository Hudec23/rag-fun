"""F-parse (R-004, R-005)."""

import httpx

from conftest import (
    PARSE,
    PLAIN,
    artifact,
    assert_valid,
    new_collection,
    run_stage,
    upload,
)


def _run(api: httpx.Client, name: str) -> str:
    f = upload(api, name)["files"][0]
    return api.post("/ingest-runs", json={"file_id": f["id"], "collection_id": new_collection(api)["id"]}).json()["id"]


def test_plain_text_markdown_headings(api: httpx.Client) -> None:
    sr = run_stage(api, "ingest", _run(api, "handbook.md"), "parse", PLAIN)
    assert sr["status"] == "done"
    art = artifact(api, sr)
    assert_valid(art, "artifacts/parse.schema.json")
    heads = [e for e in art["elements"] if e["type"] == "heading"]
    assert [h["text"] for h in heads][:2] == ["Employee Handbook", "Vacation"]
    vac = next(e for e in art["elements"] if "25 vacation days" in e["text"])
    assert vac["section_path"] == ["Employee Handbook", "Vacation"]
    assert art["full_text"][vac["char_start"] : vac["char_end"]] == vac["text"]
    assert art["docling_json_key"] is None and art["pages"] == []


def test_docling_layout_pdf_pages_and_images(api: httpx.Client) -> None:
    sr = run_stage(api, "ingest", _run(api, "q3-report.pdf"), "parse", PARSE)
    assert sr["status"] == "done", sr
    art = artifact(api, sr)
    assert_valid(art, "artifacts/parse.schema.json")
    assert [p["page_no"] for p in art["pages"]] == [1, 2]
    assert all(e["bbox"] for e in art["elements"] if e["type"] in ("text", "heading", "title"))
    assert "Revenue grew 12 percent" in art["full_text"]
    png = api.get(f"/stage-runs/{sr['id']}/pages/1")
    assert png.status_code == 200 and png.content[:8] == b"\x89PNG\r\n\x1a\n"
    assert api.get(f"/stage-runs/{sr['id']}/pages/9").json()["error"]["code"] == "PAGE_NOT_FOUND"
    assert sr["summary"]["pages"] == 2


def test_docling_ocr_on_scanned_image(api: httpx.Client) -> None:
    params = {"strategy": "docling_ocr", "extract_tables": True, "page_images": True}
    sr = run_stage(api, "ingest", _run(api, "scan-invoice.png"), "parse", params)
    assert sr["status"] == "done", sr
    art = artifact(api, sr)
    assert art["ocr_used"] is True
    assert "invoice" in art["full_text"].lower()


def test_tables_from_csv_and_docx(api: httpx.Client) -> None:
    csv = artifact(api, run_stage(api, "ingest", _run(api, "prices.csv"), "parse", PLAIN))
    table = next(e for e in csv["elements"] if e["type"] == "table")
    assert table["table"]["num_rows"] == 4 and table["table"]["num_cols"] == 3
    docx = artifact(api, run_stage(api, "ingest", _run(api, "contract.docx"), "parse", PARSE))
    assert any(e["type"] == "table" and "Notice period" in e["text"] for e in docx["elements"])


def test_plain_text_rejects_images(api: httpx.Client) -> None:
    sr = run_stage(api, "ingest", _run(api, "scan-invoice.png"), "parse", PLAIN)
    assert sr["status"] == "failed"
    assert sr["error"]["code"] == "UNSUPPORTED_FOR_STRATEGY"
    assert api.get(f"/stage-runs/{sr['id']}/artifact").json()["error"]["code"] == "ARTIFACT_NOT_FOUND"
