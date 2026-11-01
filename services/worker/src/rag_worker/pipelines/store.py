from typing import Any

from haystack import Document, Pipeline


def build_store_pipeline(document_store: Any) -> Pipeline:
    """'writer' = DocumentWriter(document_store, policy=DuplicatePolicy.OVERWRITE)."""
    raise NotImplementedError("not implemented")


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
    raise NotImplementedError("not implemented")
