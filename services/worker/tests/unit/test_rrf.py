"""Unit tests for RRF fusion (services/worker/src/rag_worker/components/rrf.py):
RRFJoiner fuses per-query dense and sparse ranked document lists by Reciprocal
Rank Fusion (score(d) = sum of 1/(rrf_k + rank) over every list containing d).
The module is a stub raising NotImplementedError, so every test here is red until
T-worker-031 lands."""

from typing import Any

from haystack import Document

from rag_worker.components.rrf import RRFJoiner


def _doc(doc_id: str) -> Document:
    return Document(id=doc_id, content=f"text of {doc_id}")


def _fuse(
    lists: list[tuple[int, str, list[Document]]], rrf_k: int = 60, top_k: int = 10
) -> list[dict[str, Any]]:
    return RRFJoiner(rrf_k=rrf_k, top_k=top_k).run(lists=lists)["fused"]


def test_fused_order_and_score_of_common_doc() -> None:
    a, b, c = _doc("a"), _doc("b"), _doc("c")
    lists = [(0, "dense", [a, b]), (0, "sparse", [b, c])]
    fused = _fuse(lists, rrf_k=60, top_k=10)
    assert [entry["doc"].id for entry in fused] == ["b", "a", "c"]
    assert fused[0]["score"] == round(1 / 62 + 1 / 61, 6)
    assert fused[1]["score"] == round(1 / 61, 6)


def test_source_ranks_in_input_list_order() -> None:
    a, b, c = _doc("a"), _doc("b"), _doc("c")
    lists = [(0, "dense", [a, b]), (0, "sparse", [b, c])]
    fused = _fuse(lists, rrf_k=60, top_k=10)
    [entry] = (e for e in fused if e["doc"].id == "b")
    assert entry["source_ranks"] == [
        {"query_index": 0, "list": "dense", "rank": 2},
        {"query_index": 0, "list": "sparse", "rank": 1},
    ]


def test_ties_broken_by_doc_id_ascending() -> None:
    alpha, beta = _doc("alpha"), _doc("beta")
    # both docs appear at rank 1 in one list and rank 2 in the other: tied scores
    lists = [(0, "dense", [beta, alpha]), (0, "sparse", [alpha, beta])]
    fused = _fuse(lists, rrf_k=60, top_k=10)
    assert [entry["doc"].id for entry in fused] == ["alpha", "beta"]
    assert fused[0]["score"] == fused[1]["score"] == round(1 / 61 + 1 / 62, 6)


def test_top_k_truncates_fused_list() -> None:
    lists = [(0, "dense", [_doc("a"), _doc("b"), _doc("c"), _doc("d")])]
    fused = _fuse(lists, rrf_k=60, top_k=2)
    assert [entry["doc"].id for entry in fused] == ["a", "b"]
    assert fused[0]["score"] == round(1 / 61, 6)
    assert fused[1]["score"] == round(1 / 62, 6)


def test_two_queries_contribute_to_same_doc() -> None:
    x, y, z = _doc("x"), _doc("y"), _doc("z")
    lists = [(0, "dense", [x, y]), (1, "sparse", [x, z])]
    fused = _fuse(lists, rrf_k=60, top_k=10)
    assert fused[0]["doc"].id == "x"
    assert fused[0]["score"] == round(1 / 61 + 1 / 61, 6)
    assert fused[0]["source_ranks"] == [
        {"query_index": 0, "list": "dense", "rank": 1},
        {"query_index": 1, "list": "sparse", "rank": 1},
    ]


def test_empty_input_returns_empty_list() -> None:
    assert _fuse([], rrf_k=60, top_k=10) == []
