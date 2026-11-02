from typing import Any

import numpy as np


def chunk_stats(char_counts: list[int]) -> dict[str, Any]:
    """chunk artifact 'stats': count, min_chars, max_chars, mean_chars (round 2), histogram =
    numpy.histogram(char_counts, bins=min(20, max(1, count))) with bin_edges rounded to 2 decimals.
    Empty list -> count 0, min/max/mean 0, bin_edges [], counts []."""
    count = len(char_counts)
    if count == 0:
        return {
            "count": 0,
            "min_chars": 0,
            "max_chars": 0,
            "mean_chars": 0,
            "histogram": {"bin_edges": [], "counts": []},
        }
    hist_counts, bin_edges = np.histogram(char_counts, bins=min(20, max(1, count)))
    return {
        "count": count,
        "min_chars": min(char_counts),
        "max_chars": max(char_counts),
        "mean_chars": round(sum(char_counts) / count, 2),
        "histogram": {
            "bin_edges": [round(float(edge), 2) for edge in bin_edges],
            "counts": [int(c) for c in hist_counts],
        },
    }
