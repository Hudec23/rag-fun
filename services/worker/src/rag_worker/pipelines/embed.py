"""Embed pipeline + embed artifact: build_embed_pipeline assembles the Haystack pipeline
('dense' -> 'sparse' -> 'tokens'), embed_artifact normalizes the embedded Documents to
contracts/artifacts/embed.schema.json."""

from typing import Any

from haystack import Pipeline

from rag_worker.components.token_view import TokenView
from rag_worker.contracts_gen.shared.common_schema import CollectionRef
from rag_worker.errors import WorkerError
from rag_worker.models.registry import TOKENIZERS, ModelSet
from rag_worker.viz.projection import pca, umap_project
from rag_worker.viz.sampling import sample_indices
from rag_worker.viz.similarity import cosine_matrix


def build_embed_pipeline(collection: CollectionRef, batch_size: int, models: ModelSet) -> Pipeline:
    """'dense' (models.dense_document_embedder(collection.dense, batch_size)) -> 'sparse'
    (models.sparse_document_embedder(collection.sparse_model)) -> 'tokens' (TokenView(models.tokenizer
    (collection.dense.model), max_tokens from registry.TOKENIZERS))."""
    entry = TOKENIZERS.get(collection.dense.model)
    if entry is None:
        raise WorkerError("MODEL_NOT_AVAILABLE", details={"model": collection.dense.model})
    _repo, max_tokens = entry
    pipeline = Pipeline()
    pipeline.add_component("dense", models.dense_document_embedder(collection.dense, batch_size))
    pipeline.add_component("sparse", models.sparse_document_embedder(collection.sparse_model))
    tokens: Any = TokenView(models.tokenizer(collection.dense.model), max_tokens)
    # tokenizer is a tokenizers.Tokenizer, not serializable: primitives only (default_to_dict shape)
    tokens.to_dict = lambda: {
        "type": "rag_worker.components.token_view.TokenView",
        "init_parameters": {"max_tokens": max_tokens},
    }
    pipeline.add_component("tokens", tokens)
    pipeline.connect("dense.documents", "sparse.documents")
    pipeline.connect("sparse.documents", "tokens.documents")
    return pipeline


def embed_artifact(
    documents: list[Any], collection: CollectionRef, tokenizer_repo: str, max_tokens: int
) -> dict[str, Any]:
    """Embedded Documents (chunk order) -> embed artifact (contracts/artifacts/embed.schema.json):
    chunks [{index, doc_id, dense (round 6), sparse {indices, values (round 6)}, tokens, token_count,
    over_limit}], sample_indices (viz.sampling), projections (viz.projection pca 2/3 + umap 2/3 over the
    sample), similarity (viz.similarity over the sample)."""
    chunks: list[dict[str, Any]] = []
    for index, doc in enumerate(documents):
        sparse = doc.sparse_embedding
        chunks.append(
            {
                "index": index,
                "doc_id": doc.meta["doc_id"],
                "dense": [round(value, 6) for value in (doc.embedding or [])],
                "sparse": {
                    "indices": list(sparse.indices),
                    "values": [round(value, 6) for value in sparse.values],
                },
                "tokens": list(doc.meta["tokens"]),
                "token_count": int(doc.meta["token_count"]),
                "over_limit": bool(doc.meta["over_limit"]),
            }
        )
    sample = sample_indices(len(documents))
    vectors = [chunks[index]["dense"] for index in sample]
    pca2, _ = pca(vectors, 2)
    pca3, variance = pca(vectors, 3)
    return {
        "schema_version": 1,
        "stage": "embed",
        "dense_model": collection.dense.model,
        "dense_dims": collection.dense.dims,
        "max_tokens": max_tokens,
        "sparse_model": collection.sparse_model,
        "tokenizer": tokenizer_repo,
        "chunks": chunks,
        "sample_indices": sample,
        "projections": {
            "pca2": pca2,
            "pca3": pca3,
            "pca_explained_variance": variance,
            "umap2": umap_project(vectors, 2),
            "umap3": umap_project(vectors, 3),
        },
        "similarity": cosine_matrix(vectors),
    }
