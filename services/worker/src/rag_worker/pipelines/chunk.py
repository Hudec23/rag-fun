from typing import Any

from haystack import Pipeline

from rag_worker.contracts_gen.shared.common_schema import DenseModelConfig
from rag_worker.models.registry import ModelSet


def build_chunk_pipeline(
    strategy: str, params: dict[str, Any], models: ModelSet, dense: DenseModelConfig
) -> Pipeline:
    """'splitter' -> 'annotator' (ChunkAnnotator; splitter.documents -> annotator.documents).
    fixed + split_by word: DocumentSplitter(split_by='word', split_length=length, split_overlap=overlap).
    fixed + split_by char: DocumentSplitter(split_by='function', splitting_function=chars (module-level
    `def chars(text): return list(text)`), split_length=length, split_overlap=overlap) — exact character
    windows. sentence: DocumentSplitter(split_by='sentence', split_length, split_overlap, language='en').
    recursive: RecursiveDocumentSplitter(split_length, split_overlap, split_unit='char', separators).
    semantic: SemanticSplitter(models.dense_text_embedder(dense), breakpoint_percentile, min_sentences,
    max_sentences). structure: StructureChunker(models.tokenizer(dense.model), max_tokens, merge_peers)
    — input docling_json. table: TableChunker(row_chunks, text_length, text_overlap) — input elements +
    source_text. Every splitter: from haystack.components.preprocessors import DocumentSplitter,
    RecursiveDocumentSplitter."""
    raise NotImplementedError("not implemented")


def run_chunk(
    pipeline: Pipeline,
    strategy: str,
    parse_artifact: dict[str, Any],
    docling_json: str | None,
    file_id: str,
) -> dict[str, Any]:
    """Feed the pipeline per strategy (fixed/sentence/recursive/semantic: documents=[Document(
    content=full_text)]; structure: docling_json (None -> WorkerError('UNSUPPORTED_FOR_STRATEGY',
    details={'parse_strategy': 'plain_text'})); table: elements + source_text); annotator also gets
    elements, source_text = full_text, file_id. -> {'chunks': [...], 'semantic': dict | None}."""
    raise NotImplementedError("not implemented")
