from typing import Any


def chunk_stats(char_counts: list[int]) -> dict[str, Any]:
    """chunk artifact 'stats': count, min_chars, max_chars, mean_chars (round 2), histogram =
    numpy.histogram(char_counts, bins=min(20, max(1, count))) with bin_edges rounded to 2 decimals.
    Empty list -> count 0, min/max/mean 0, bin_edges [], counts []."""
    raise NotImplementedError("not implemented")
