from typing import Any

from haystack import Document, component


def rrf_fuse(
    lists: list[tuple[int, str, list[Document]]], rrf_k: int, top_k: int
) -> list[dict[str, Any]]:
    """lists = [(query_index, 'dense'|'sparse', ranked docs)]. score(d) = Σ 1/(rrf_k + rank) over
    every list containing d (rank 1-based; identity = doc.id). Sort score desc, then doc.id asc;
    keep top_k. Returns [{'doc': Document, 'score': float(round 6), 'source_ranks':
    [{'query_index', 'list', 'rank'}]}] with source_ranks in input-list order."""
    raise NotImplementedError("not implemented")


@component
class RRFJoiner:
    def __init__(self, rrf_k: int, top_k: int) -> None:
        self.rrf_k = rrf_k
        self.top_k = top_k

    @component.output_types(fused=list[dict[str, Any]])
    def run(self, lists: list[tuple[int, str, list[Document]]]) -> dict[str, Any]:
        return {"fused": rrf_fuse(lists, self.rrf_k, self.top_k)}
