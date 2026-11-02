from typing import Any

from haystack import Document, Pipeline
from haystack.components.writers import DocumentWriter
from haystack.dataclasses import SparseEmbedding
from haystack.document_stores.types import DuplicatePolicy

from rag_worker.errors import WorkerError


def build_store_pipeline(document_store: Any) -> Pipeline:
    """'writer' = DocumentWriter(document_store, policy=DuplicatePolicy.OVERWRITE)."""
    pipeline = Pipeline()
    pipeline.add_component(
        "writer", DocumentWriter(document_store, policy=DuplicatePolicy.OVERWRITE)
    )
    return pipeline


def documents_for_store(
    chunk_artifact: dict[str, Any],
    embed_artifact: dict[str, Any],
    meta_base: dict[str, Any],
    stored_at: str,
) -> list[Document]:
    """One Document per chunk: id = chunk doc_id, content = chunk text, embedding = dense,
    sparse_embedding = SparseEmbedding(indices, values), meta = payload Meta
    (contracts/qdrant/payload.schema.json): meta_base (file_id, batch_id, batch_name, filename, mime,
    tags, ingest_run_id, dense_model, sparse_model, parse_strategy, chunk_strategy) + page (first of
    page_numbers or None), page_numbers, section_path, element_type, chunk_index, stored_at.
    Chunk/embed index mismatch -> WorkerError('VALIDATION_ERROR', details={'reason': 'chunk/embed mismatch'})."""
    chunks: list[dict[str, Any]] = chunk_artifact["chunks"]
    embeds: list[dict[str, Any]] = embed_artifact["chunks"]
    if len(chunks) != len(embeds) or any(
        chunk["doc_id"] != embed["doc_id"] for chunk, embed in zip(chunks, embeds, strict=True)
    ):
        raise WorkerError("VALIDATION_ERROR", details={"reason": "chunk/embed mismatch"})
    documents: list[Document] = []
    for chunk, embed in zip(chunks, embeds, strict=True):
        page_numbers: list[int] = chunk["page_numbers"]
        documents.append(
            Document(
                id=chunk["doc_id"],
                content=chunk["text"],
                embedding=embed["dense"],
                sparse_embedding=SparseEmbedding(
                    indices=embed["sparse"]["indices"],
                    values=embed["sparse"]["values"],
                ),
                meta={
                    **meta_base,
                    "page": page_numbers[0] if page_numbers else None,
                    "page_numbers": page_numbers,
                    "section_path": chunk["section_path"],
                    "element_type": chunk["element_type"],
                    "chunk_index": chunk["index"],
                    "stored_at": stored_at,
                },
            )
        )
    return documents
