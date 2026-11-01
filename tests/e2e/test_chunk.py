"""F-chunk (R-006, R-007)."""

import httpx
import pytest

from conftest import (
    PARSE,
    PLAIN,
    artifact,
    assert_valid,
    new_collection,
    run_stage,
    upload,
)

STRATEGIES = {
    "fixed": {"strategy": "fixed", "split_by": "word", "length": 12, "overlap": 3},
    "sentence": {"strategy": "sentence", "length": 2, "overlap": 0},
    "recursive": {"strategy": "recursive", "length": 120, "overlap": 20, "separators": ["\n\n", "sentence", "\n", " "]},
    "semantic": {"strategy": "semantic", "breakpoint_percentile": 60, "min_sentences": 1, "max_sentences": 4},
    "structure": {"strategy": "structure", "max_tokens": 64, "merge_peers": True},
    "table": {"strategy": "table", "row_chunks": True, "text_length": 200, "text_overlap": 20},
}


def _parsed(api: httpx.Client, name: str, parse: dict) -> str:  # type: ignore[type-arg]
    f = upload(api, name)["files"][0]
    rid = api.post("/ingest-runs", json={"file_id": f["id"], "collection_id": new_collection(api)["id"]}).json()["id"]
    assert run_stage(api, "ingest", rid, "parse", parse)["status"] == "done"
    return rid


@pytest.mark.parametrize("strategy", list(STRATEGIES))
def test_every_strategy_produces_valid_chunks(api: httpx.Client, strategy: str) -> None:
    name = "contract.docx" if strategy == "table" else "q3-report.pdf"
    rid = _parsed(api, name, PARSE)
    sr = run_stage(api, "ingest", rid, "chunk", STRATEGIES[strategy])
    assert sr["status"] == "done", sr
    art = artifact(api, sr)
    assert_valid(art, "artifacts/chunk.schema.json")
    assert art["strategy"] == strategy and art["stats"]["count"] == len(art["chunks"]) > 0
    assert sr["summary"]["chunks"] == len(art["chunks"])
    for c in art["chunks"]:
        if c["char_start"] is not None:
            assert art["source_text"][c["char_start"] : c["char_end"]] == c["text"]
    if strategy == "semantic":
        assert art["semantic"] and art["semantic"]["gaps"]
    if strategy == "table":
        assert any(c["element_type"] == "table" for c in art["chunks"])


def test_fixed_word_windows_overlap(api: httpx.Client) -> None:
    rid = _parsed(api, "notes.txt", PLAIN)
    art = artifact(api, run_stage(api, "ingest", rid, "chunk", {"strategy": "fixed", "split_by": "word", "length": 4, "overlap": 2}))
    words = [c["text"].split() for c in art["chunks"]]
    assert all(len(w) <= 4 for w in words)
    assert words[0][2:] == words[1][:2]  # 2-word overlap


def test_structure_needs_docling_parse(api: httpx.Client) -> None:
    rid = _parsed(api, "handbook.md", PLAIN)
    sr = run_stage(api, "ingest", rid, "chunk", STRATEGIES["structure"])
    assert sr["status"] == "failed" and sr["error"]["code"] == "UNSUPPORTED_FOR_STRATEGY"
