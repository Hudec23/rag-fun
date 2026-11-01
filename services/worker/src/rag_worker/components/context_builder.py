from typing import Any


def select_context(
    hits: list[dict[str, Any]], token_counts: list[int], budget_tokens: int
) -> tuple[list[dict[str, Any]], int, int]:
    """Greedy in rank order: include hit i while used + token_counts[i] <= budget_tokens; a hit that
    does not fit is skipped (dropped) and later smaller hits may still fit. Returns
    (included [{'n': 1.., 'hit': hit, 'tokens': t}], used_tokens, dropped_count)."""
    raise NotImplementedError("not implemented")


def parse_citations(answer: str, max_n: int) -> list[int]:
    """Distinct integers n from markers '[n]' or '[n, m]' / '[n,m]' in answer with 1 <= n <= max_n,
    ascending."""
    raise NotImplementedError("not implemented")
