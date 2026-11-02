"""Rerank pipeline + rerank artifact: build_rerank_pipeline wires a single 'ranker' component
from ModelSet, rerank_artifact reshapes the reranked Documents (or, when disabled, the
un-reranked before hits) into the after list of contracts/artifacts/rerank.schema.json."""

from typing import Any

from haystack import Pipeline

from rag_worker.components.hits import to_hit
from rag_worker.models.registry import ModelSet


def build_rerank_pipeline(model: str, top_n: int, models: ModelSet) -> Pipeline:
    """'ranker' = models.ranker(model, top_n)."""
    pipeline = Pipeline()
    pipeline.add_component("ranker", models.ranker(model, top_n))
    return pipeline


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
    if enabled:
        ranked = sorted(reranked or [], key=lambda doc: (-(doc.score or 0.0), doc.id))[:top_n]
        rank_of: dict[str, Any] = {hit["doc_id"]: hit["rank"] for hit in before}
        after = [
            {
                "hit": to_hit(doc, rank, doc.score),
                "previous_rank": rank_of[doc.id],
                "rerank_score": doc.score,
            }
            for rank, doc in enumerate(ranked, 1)
        ]
    else:
        after = [
            {"hit": hit, "previous_rank": hit["rank"], "rerank_score": None}
            for hit in before[:top_n]
        ]
    return {
        "schema_version": 1,
        "stage": "rerank",
        "enabled": enabled,
        "model": model if enabled else None,
        "top_n": top_n,
        "query": query,
        "before": before,
        "after": after,
    }
