"""Unit tests for context selection + citation parsing: build inputs inline, call the functions
directly, assert exact lists/ints."""

from rag_worker.components.context_builder import parse_citations, select_context

H1 = {"id": "h-1", "score": 0.9}
H2 = {"id": "h-2", "score": 0.5}
H3 = {"id": "h-3", "score": 0.3}
HITS = [H1, H2, H3]
TOKENS = [100, 50, 30]


def test_select_context_drops_big_hit_then_includes_smaller() -> None:
    included, used, dropped = select_context(HITS, TOKENS, 140)
    assert included == [
        {"n": 1, "hit": H1, "tokens": 100},
        {"n": 2, "hit": H3, "tokens": 30},
    ]
    assert used == 130
    assert dropped == 1


def test_select_context_zero_budget_drops_all() -> None:
    included, used, dropped = select_context(HITS, TOKENS, 0)
    assert included == []
    assert used == 0
    assert dropped == 3


def test_parse_citations_distinct_in_range_ascending() -> None:
    assert parse_citations("A [1] b [2, 3] c [3] d [9]", 3) == [1, 2, 3]


def test_parse_citations_single_bound_and_no_markers() -> None:
    assert parse_citations("[1,2]", 1) == [1]
    assert parse_citations("no cites", 5) == []
