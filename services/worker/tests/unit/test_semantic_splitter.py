"""Unit tests for SemanticSplitter and its pure helpers (breakpoints, group_sentences)."""

from haystack import Document

from rag_worker.components.semantic_splitter import SemanticSplitter, breakpoints, group_sentences
from rag_worker.models.fakes import FakeDenseTextEmbedder

SOURCE = "Cats purr. Cats sleep. Taxes rise. Taxes hurt."
SENTENCES_4 = ["one", "two", "three", "four"]
SENTENCES_5 = ["one", "two", "three", "four", "five"]


def test_breakpoints_threshold_and_flags() -> None:
    assert breakpoints([0.1, 0.9, 0.2], 50) == (0.2, [False, True, False])


def test_breakpoints_empty() -> None:
    assert breakpoints([], 90) == (0.0, [])


def test_group_break_after_full_group() -> None:
    assert group_sentences(SENTENCES_4, [False, True, False], 1, 10) == [[0, 1], [2, 3]]


def test_min_sentences_suppresses_early_break() -> None:
    assert group_sentences(SENTENCES_4, [True, False, False], 3, 10) == [[0, 1, 2, 3]]


def test_max_sentences_forces_splits() -> None:
    assert group_sentences(SENTENCES_5, [False, False, False, False], 1, 2) == [[0, 1], [2, 3], [4]]


def test_run_splits_document_and_reports_gaps() -> None:
    splitter = SemanticSplitter(FakeDenseTextEmbedder(64), 50, 1, 10)
    out = splitter.run(documents=[Document(content=SOURCE)])
    docs = out["documents"]
    assert len(docs) >= 2
    for doc in docs:
        assert doc.content is not None and doc.content in SOURCE
        start = doc.meta["split_idx_start"]
        assert SOURCE[start : start + len(doc.content)] == doc.content
    assert len(out["semantic"]["gaps"]) == 3
