import re
from typing import Any


def select_context(
    hits: list[dict[str, Any]], token_counts: list[int], budget_tokens: int
) -> tuple[list[dict[str, Any]], int, int]:
    """Greedy in rank order: include hit i while used + token_counts[i] <= budget_tokens; a hit that
    does not fit is skipped (dropped) and later smaller hits may still fit. Returns
    (included [{'n': 1.., 'hit': hit, 'tokens': t}], used_tokens, dropped_count)."""
    included: list[dict[str, Any]] = []
    used = 0
    dropped = 0
    for i, hit in enumerate(hits):
        tokens = token_counts[i]
        if used + tokens <= budget_tokens:
            included.append({"n": len(included) + 1, "hit": hit, "tokens": tokens})
            used += tokens
        else:
            dropped += 1
    return included, used, dropped


def parse_citations(answer: str, max_n: int) -> list[int]:
    """Distinct integers n from markers '[n]' or '[n, m]' / '[n,m]' in answer with 1 <= n <= max_n,
    ascending."""
    found: set[int] = set()
    for marker in re.finditer(r"\[([^\[\]]*)\]", answer):
        parts = [p.strip() for p in marker.group(1).split(",")]
        if parts and all(part.isdigit() for part in parts):
            for part in parts:
                n = int(part)
                if 1 <= n <= max_n:
                    found.add(n)
    return sorted(found)
