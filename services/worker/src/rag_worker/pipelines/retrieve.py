"""Retrieve pipelines: to_haystack_filters maps a PayloadFilter to Haystack filter dicts on
'meta.<key>' fields; build_retrieve_pipeline assembles dense/sparse/hybrid Haystack pipelines
(text embedder -> Qdrant retriever per branch); run_retrieve runs the pipeline per query and
returns the retriever Documents keyed by branch."""

from typing import Any

from haystack import Pipeline
from haystack_integrations.components.retrievers.qdrant import (
    QdrantEmbeddingRetriever,
    QdrantSparseEmbeddingRetriever,
)

from rag_worker.contracts_gen.shared.common_schema import (
    CollectionRef,
    FilterCondition,
    MatchAnyCondition,
    MatchValueCondition,
    PayloadFilter,
)
from rag_worker.models.registry import ModelSet

# mode -> retriever components whose outputs run_retrieve collects
RETRIEVERS: dict[str, set[str]] = {
    "dense": {"dense_retriever"},
    "sparse": {"sparse_retriever"},
    "hybrid": {"dense_retriever", "sparse_retriever"},
}


def _condition_leaves(condition: FilterCondition) -> list[dict[str, Any]]:
    """One FilterCondition -> its leaf filter dicts on 'meta.<key>' (range -> one leaf per bound)."""
    if isinstance(condition, MatchValueCondition):
        return [
            {"field": f"meta.{condition.key}", "operator": "==", "value": condition.match.value}
        ]
    if isinstance(condition, MatchAnyCondition):
        return [
            {"field": f"meta.{condition.key}", "operator": "in", "value": list(condition.match.any)}
        ]
    leaves: list[dict[str, Any]] = []
    if condition.range.gte is not None:
        leaves.append(
            {"field": f"meta.{condition.key}", "operator": ">=", "value": condition.range.gte}
        )
    if condition.range.lte is not None:
        leaves.append(
            {"field": f"meta.{condition.key}", "operator": "<=", "value": condition.range.lte}
        )
    return leaves


def to_haystack_filters(f: PayloadFilter) -> dict[str, Any] | None:
    """PayloadFilter -> Haystack filter dict on 'meta.<key>' fields. Empty -> None.
    match.value -> {'field', 'operator': '==', 'value'}; match.any -> 'in' with list; range ->
    AND of '>=' / '<='. must -> AND, should -> OR, must_not -> NOT (each AND-ed together)."""
    groups: list[dict[str, Any]] = []
    must = [leaf for c in (f.must or []) for leaf in _condition_leaves(c)]
    should = [leaf for c in (f.should or []) for leaf in _condition_leaves(c)]
    must_not = [leaf for c in (f.must_not or []) for leaf in _condition_leaves(c)]
    if must:
        groups.append({"operator": "AND", "conditions": must})
    if should:
        groups.append({"operator": "OR", "conditions": should})
    if must_not:
        groups.append(
            {"operator": "NOT", "conditions": [{"operator": "AND", "conditions": must_not}]}
        )
    if not groups:
        return None
    if len(groups) == 1:
        return groups[0]
    return {"operator": "AND", "conditions": groups}


def build_retrieve_pipeline(
    mode: str, collection: CollectionRef, document_store: Any, top_k: int, models: ModelSet
) -> Pipeline:
    """dense: 'dense_embedder' (models.dense_text_embedder) -> 'dense_retriever'
    (QdrantEmbeddingRetriever(document_store, top_k)). sparse: 'sparse_embedder' -> 'sparse_retriever'
    (QdrantSparseEmbeddingRetriever). hybrid: both branches (no joiner in the pipeline; RRF runs after,
    per SYSTEM.md the graph shows both retrievers)."""
    pipeline = Pipeline()
    if mode in ("dense", "hybrid"):
        pipeline.add_component("dense_embedder", models.dense_text_embedder(collection.dense))
        pipeline.add_component(
            "dense_retriever", QdrantEmbeddingRetriever(document_store=document_store, top_k=top_k)
        )
        pipeline.connect("dense_embedder.embedding", "dense_retriever.query_embedding")
    if mode in ("sparse", "hybrid"):
        pipeline.add_component(
            "sparse_embedder", models.sparse_text_embedder(collection.sparse_model)
        )
        pipeline.add_component(
            "sparse_retriever",
            QdrantSparseEmbeddingRetriever(document_store=document_store, top_k=top_k),
        )
        pipeline.connect(
            "sparse_embedder.sparse_embedding", "sparse_retriever.query_sparse_embedding"
        )
    return pipeline


def run_retrieve(
    pipeline: Pipeline, mode: str, queries: list[str], filters: dict[str, Any] | None
) -> list[dict[str, Any]]:
    """For each query run the pipeline -> [{'query', 'dense': [Document] | None, 'sparse': [...] | None}]."""
    results: list[dict[str, Any]] = []
    for query in queries:
        data: dict[str, Any] = {"text": query}
        if filters is not None:
            data["filters"] = filters
        output = pipeline.run(data, include_outputs_from=RETRIEVERS.get(mode, RETRIEVERS["hybrid"]))
        results.append(
            {
                "query": query,
                "dense": output["dense_retriever"]["documents"]
                if mode in ("dense", "hybrid")
                else None,
                "sparse": output["sparse_retriever"]["documents"]
                if mode in ("sparse", "hybrid")
                else None,
            }
        )
    return results
