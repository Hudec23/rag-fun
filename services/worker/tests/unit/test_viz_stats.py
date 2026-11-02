"""Unit tests for rag_worker.viz.stats.chunk_stats: exact dicts, call the function directly."""

from rag_worker.viz.stats import chunk_stats


def test_chunk_stats_empty_list() -> None:
    assert chunk_stats([]) == {
        "count": 0,
        "min_chars": 0,
        "max_chars": 0,
        "mean_chars": 0,
        "histogram": {"bin_edges": [], "counts": []},
    }


def test_chunk_stats_single_value() -> None:
    res = chunk_stats([10])
    assert res["count"] == 1
    assert res["min_chars"] == 10
    assert res["max_chars"] == 10
    assert res["mean_chars"] == 10.0
    counts = res["histogram"]["counts"]
    assert len(counts) == 1
    assert sum(counts) == 1


def test_chunk_stats_four_values_have_four_bins() -> None:
    res = chunk_stats([10, 20, 30, 40])
    assert res["mean_chars"] == 25.0
    assert len(res["histogram"]["counts"]) == 4
    bin_edges = list(res["histogram"]["bin_edges"])
    assert len(bin_edges) == 5
    assert bin_edges[0] == 10.0
    assert bin_edges[-1] == 40.0
    assert bin_edges == [10.0, 17.5, 25.0, 32.5, 40.0]


def test_chunk_stats_caps_bins_at_20() -> None:
    res = chunk_stats(list(range(1, 26)))
    assert res["count"] == 25
    assert len(res["histogram"]["counts"]) == 20
    assert sum(res["histogram"]["counts"]) == 25
    assert len(res["histogram"]["bin_edges"]) == 21


def test_chunk_stats_mean_rounded_to_two_decimals() -> None:
    assert chunk_stats([1, 2, 2])["mean_chars"] == 1.67
