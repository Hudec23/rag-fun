from typing import Any

from haystack import Document, component


def rrf_fuse(
    lists: list[tuple[int, str, list[Document]]], rrf_k: int, top_k: int
) -> list[dict[str, Any]]:
    """lists = [(query_index, 'dense'|'sparse', ranked docs)]. score(d) = Σ 1/(rrf_k + rank) over
    every list containing d (rank 1-based; identity = doc.id). Sort score desc, then doc.id asc;
    keep top_k. Returns [{'doc': Document, 'score': float(round 6), 'source_ranks':
    [{'query_index', 'list', 'rank'}]}] with source_ranks in input-list order."""
    docs: dict[str, Document] = {}
    scores: dict[str, float] = {}
    source_ranks: dict[str, list[dict[str, Any]]] = {}
    for query_index, list_name, docs_in_list in lists:
        for rank, doc in enumerate(docs_in_list, start=1):
            key = doc.id
            if key not in docs:
                docs[key] = doc
                scores[key] = 0.0
                source_ranks[key] = []
            scores[key] += 1.0 / (rrf_k + rank)
            source_ranks[key].append({"query_index": query_index, "list": list_name, "rank": rank})
    ranked = sorted(docs, key=lambda key: (-round(scores[key], 6), key))
    return [
        {
            "doc": docs[key],
            "score": round(scores[key], 6),
            "source_ranks": source_ranks[key],
        }
        for key in ranked[:top_k]
    ]


@component
class RRFJoiner:
    def __init__(self, rrf_k: int, top_k: int) -> None:
        self.rrf_k = rrf_k
        self.top_k = top_k

    @component.output_types(fused=list[dict[str, Any]])
    def run(self, lists: list[tuple[int, str, list[Document]]]) -> dict[str, Any]:
        return {"fused": rrf_fuse(lists, self.rrf_k, self.top_k)}
