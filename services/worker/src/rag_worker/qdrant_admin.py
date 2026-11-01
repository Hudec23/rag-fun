"""Qdrant writes owned by the worker (collection lifecycle, deletes). Sync qdrant_client.QdrantClient;
call from asyncio.to_thread."""

from typing import Any

from qdrant_client import QdrantClient

KEYWORD_INDEXES = [
    "meta.file_id",
    "meta.batch_id",
    "meta.tags",
    "meta.mime",
    "meta.element_type",
    "meta.chunk_strategy",
    "meta.parse_strategy",
]
INTEGER_INDEXES = ["meta.page", "meta.chunk_index"]


def document_store(qdrant_url: str, qdrant_name: str, dims: int) -> Any:
    """QdrantDocumentStore(url=qdrant_url, index=qdrant_name, embedding_dim=dims, similarity='cosine',
    use_sparse_embeddings=True, sparse_idf=True, recreate_index=False, return_embedding=False,
    wait_result_from_api=True, payload_fields_to_index=[{'field_name': k, 'field_schema': 'keyword'}
    for KEYWORD_INDEXES] + [... 'integer' for INTEGER_INDEXES])."""
    raise NotImplementedError("not implemented")


def delete_file_points(client: QdrantClient, qdrant_name: str, file_id: str) -> int:
    """Delete points with meta.file_id == file_id; return how many existed before (count exact).
    Missing collection -> 0."""
    raise NotImplementedError("not implemented")


def drop_collection(client: QdrantClient, qdrant_name: str) -> None:
    """Delete collection if it exists."""
    raise NotImplementedError("not implemented")
