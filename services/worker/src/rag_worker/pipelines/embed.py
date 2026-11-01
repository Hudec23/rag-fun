from typing import Any

from haystack import Pipeline

from rag_worker.contracts_gen.shared.common_schema import CollectionRef
from rag_worker.models.registry import ModelSet


def build_embed_pipeline(collection: CollectionRef, batch_size: int, models: ModelSet) -> Pipeline:
    """'dense' (models.dense_document_embedder(collection.dense, batch_size)) -> 'sparse'
    (models.sparse_document_embedder(collection.sparse_model)) -> 'tokens' (TokenView(models.tokenizer
    (collection.dense.model), max_tokens from registry.TOKENIZERS))."""
    raise NotImplementedError("not implemented")


def embed_artifact(
    documents: list[Any], collection: CollectionRef, tokenizer_repo: str, max_tokens: int
) -> dict[str, Any]:
    """Embedded Documents (chunk order) -> embed artifact (contracts/artifacts/embed.schema.json):
    chunks [{index, doc_id, dense (round 6), sparse {indices, values (round 6)}, tokens, token_count,
    over_limit}], sample_indices (viz.sampling), projections (viz.projection pca 2/3 + umap 2/3 over the
    sample), similarity (viz.similarity over the sample)."""
    raise NotImplementedError("not implemented")
