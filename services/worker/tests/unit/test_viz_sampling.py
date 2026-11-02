"""Unit tests for rag_worker.viz.sampling.sample_indices: pure function, assert exact lists."""

from rag_worker.viz.sampling import sample_indices


def test_sample_indices_empty_and_single() -> None:
    assert sample_indices(0) == []
    assert sample_indices(1) == [0]


def test_sample_indices_small_n_returns_full_range() -> None:
    assert sample_indices(5) == [0, 1, 2, 3, 4]


def test_sample_indices_large_n_capped_at_200() -> None:
    idx = sample_indices(1000)
    assert len(idx) == 200
    assert idx[0] == 0
    assert idx[-1] == 999
    assert all(isinstance(x, int) for x in idx)
    assert all(a < b for a, b in zip(idx, idx[1:], strict=False))


def test_sample_indices_explicit_cap_rounds_linspace() -> None:
    idx = sample_indices(10, cap=3)
    assert idx == [0, 4, 9]
    assert len(idx) == 3
    assert idx[0] == 0
    assert idx[-1] == 9
    assert len(set(idx)) == len(idx)
