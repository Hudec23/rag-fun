"""Parse pipelines (strategies 'plain_text', 'docling_layout', 'docling_ocr'): build each pipeline
with build_parse_pipeline, feed a SAMPLES file through run_parse, assert the exact output dict.
Real Docling models (baked into worker-dev, slow). The parse module is a stub — every test here is
red until T-worker-016."""

import json
from typing import Any

import pytest

from rag_worker.errors import WorkerError
from rag_worker.pipelines.parse import build_parse_pipeline, run_parse
from tests.conftest import SAMPLES

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
OUTPUT_KEYS = {"elements", "pages", "page_images", "ocr_used", "docling_json"}
LAYOUT_PARAMS: dict[str, Any] = {
    "strategy": "docling_layout",
    "extract_tables": True,
    "page_images": True,
}
NO_PAGE_IMAGE_PARAMS: dict[str, Any] = {
    "strategy": "docling_layout",
    "extract_tables": True,
    "page_images": False,
}
OCR_PARAMS: dict[str, Any] = {
    "strategy": "docling_ocr",
    "extract_tables": True,
    "page_images": True,
}
PLAIN_PARAMS: dict[str, Any] = {"strategy": "plain_text"}


def _run(strategy: str, params: dict[str, Any], name: str, mime: str) -> dict[str, Any]:
    pipeline = build_parse_pipeline(strategy, params)
    return run_parse(pipeline, strategy, (SAMPLES / name).read_bytes(), mime, name)


def test_plain_text_pipeline_on_handbook_md() -> None:
    out = _run("plain_text", PLAIN_PARAMS, "handbook.md", "text/markdown")

    assert set(out) == OUTPUT_KEYS
    assert out["pages"] == []
    assert out["page_images"] == {}
    assert out["docling_json"] is None
    assert out["ocr_used"] is False
    assert out["elements"]
    assert [e["text"] for e in out["elements"]][:2] == ["Employee Handbook", "Vacation"]


def test_docling_layout_pdf_pages_and_page_images() -> None:
    out = _run("docling_layout", LAYOUT_PARAMS, "q3-report.pdf", "application/pdf")

    assert set(out) == OUTPUT_KEYS
    assert [p["page_no"] for p in out["pages"]] == [1, 2]
    assert set(out["page_images"]) == {1, 2}
    for image in out["page_images"].values():
        assert image[:8] == PNG_MAGIC
    assert isinstance(out["docling_json"], str)
    assert isinstance(json.loads(out["docling_json"]), dict)
    assert any("Revenue grew 12 percent" in e["text"] for e in out["elements"])


def test_docling_layout_page_images_false_returns_no_images() -> None:
    out = _run("docling_layout", NO_PAGE_IMAGE_PARAMS, "q3-report.pdf", "application/pdf")

    assert out["page_images"] == {}
    assert [p["page_no"] for p in out["pages"]] == [1, 2]


def test_docling_ocr_scanned_image_marks_ocr_used() -> None:
    out = _run("docling_ocr", OCR_PARAMS, "scan-invoice.png", "image/png")

    assert out["ocr_used"] is True
    joined = "\n".join(e["text"] for e in out["elements"]).lower()
    assert "invoice" in joined


def test_corrupted_pdf_raises_parse_failed() -> None:
    pipeline = build_parse_pipeline("docling_layout", LAYOUT_PARAMS)

    with pytest.raises(WorkerError) as excinfo:
        run_parse(pipeline, "docling_layout", b"%PDF-1.4 garbage", "application/pdf", "corrupt.pdf")
    assert excinfo.value.code == "PARSE_FAILED"
    reason = excinfo.value.details["reason"]
    assert isinstance(reason, str)
    assert 0 < len(reason) <= 300


def test_pipeline_component_names() -> None:
    docling = build_parse_pipeline("docling_layout", LAYOUT_PARAMS)
    assert set(docling.graph.nodes) == {"converter", "extractor"}

    plain = build_parse_pipeline("plain_text", PLAIN_PARAMS)
    assert set(plain.graph.nodes) == {"converter"}
