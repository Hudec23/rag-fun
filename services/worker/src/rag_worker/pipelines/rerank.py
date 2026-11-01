from typing import Any

from haystack import Pipeline

from rag_worker.models.registry import ModelSet


def build_rerank_pipeline(model: str, top_n: int, models: ModelSet) -> Pipeline:
    """'ranker' = models.ranker(model, top_n)."""
    raise NotImplementedError("not implemented")


def rerank_artifact(
    enabled: bool,
    model: str | None,
    top_n: int,
    query: str,
    before: list[dict[str, Any]],
    reranked: list[Any] | None,
) -> dict[str, Any]:
    """contracts/artifacts/rerank.schema.json. enabled: after[i] = {'hit': to_hit(doc, rank i+1,
    score), 'previous_rank': rank of doc_id in before, 'rerank_score': score}; ties already ordered by
    the ranker, re-sort score desc then doc_id asc. disabled: after = before[:top_n] with
    previous_rank = rank, rerank_score None, model None."""
    raise NotImplementedError("not implemented")
