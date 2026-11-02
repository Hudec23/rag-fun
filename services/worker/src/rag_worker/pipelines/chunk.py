"""Chunk pipelines (strategies fixed / sentence / recursive / semantic / structure / table):
build_chunk_pipeline assembles the Haystack pipeline ('splitter' -> 'annotator'), run_chunk feeds
it per strategy and normalizes the result to {'chunks', 'semantic'}."""

import re
from typing import Any

from haystack import Document, Pipeline
from haystack.components.preprocessors import DocumentSplitter, RecursiveDocumentSplitter

from rag_worker.components.chunk_annotator import ChunkAnnotator
from rag_worker.components.semantic_splitter import SemanticSplitter
from rag_worker.components.structure_chunker import StructureChunker
from rag_worker.components.table_chunker import TableChunker
from rag_worker.contracts_gen.shared.common_schema import DenseModelConfig
from rag_worker.errors import WorkerError
from rag_worker.models.registry import ModelSet


def chars(text: str) -> list[str]:
    """Exact character units for DocumentSplitter(split_by='function')."""
    return list(text)


def fixed_char_windows(text: str, length: int, overlap: int) -> list[str]:
    """Exact windows over chars(text): `length` chars each, stepping by length - overlap."""
    units = chars(text)
    step = max(length - overlap, 1)
    return ["".join(units[i : i + length]) for i in range(0, len(units), step)]


def fixed_word_windows(text: str, length: int, overlap: int) -> list[str]:
    """Exact windows over the text's words: `length` words each, stepping by length - overlap."""
    spans = [match.span() for match in re.finditer(r"\S+", text)]
    step = max(length - overlap, 1)
    return [
        text[spans[i][0] : spans[min(i + length - 1, len(spans) - 1)][1]]
        for i in range(0, len(spans), step)
    ]


def build_chunk_pipeline(
    strategy: str, params: dict[str, Any], models: ModelSet, dense: DenseModelConfig
) -> Pipeline:
    """'splitter' -> 'annotator' (ChunkAnnotator; splitter.documents -> annotator.documents).
    fixed + split_by word/char: DocumentSplitter(split_by='function') whose splitting function yields
    exact-substring windows (fixed_word_windows / fixed_char_windows over chars) of `length` words/chars
    stepping by length - overlap, so every chunk is a verbatim slice of the source and its span comes
    from split_idx_start. split_by outside {word, char}: WorkerError('UNSUPPORTED_FOR_STRATEGY').
    sentence: DocumentSplitter(split_by='sentence', split_length, split_overlap, language='en').
    recursive: RecursiveDocumentSplitter(split_length, split_overlap, split_unit='char', separators).
    semantic: SemanticSplitter(models.dense_text_embedder(dense), breakpoint_percentile, min_sentences,
    max_sentences). structure: StructureChunker(models.tokenizer(dense.model), max_tokens, merge_peers)
    — input docling_json. table: TableChunker(row_chunks, text_length, text_overlap) — input elements +
    source_text. Every splitter: from haystack.components.preprocessors import DocumentSplitter,
    RecursiveDocumentSplitter."""
    splitter: Any
    if strategy == "fixed":
        split_by = params["split_by"]
        if split_by not in ("word", "char"):
            raise WorkerError("UNSUPPORTED_FOR_STRATEGY", details={"split_by": split_by})
        windows = fixed_word_windows if split_by == "word" else fixed_char_windows
        splitter = DocumentSplitter(
            split_by="function",
            splitting_function=lambda text: windows(text, params["length"], params["overlap"]),
        )
        # the window function is a closure over length/overlap, not serializable by path:
        # primitives only (default_to_dict shape)
        splitter.to_dict = lambda: {
            "type": "haystack.components.preprocessors.document_splitter.DocumentSplitter",
            "init_parameters": {
                "split_by": "function",
                "split_length": params["length"],
                "split_overlap": params["overlap"],
            },
        }
    elif strategy == "sentence":
        splitter = DocumentSplitter(
            split_by="sentence",
            split_length=params["length"],
            split_overlap=params["overlap"],
            language="en",
        )
    elif strategy == "recursive":
        splitter = RecursiveDocumentSplitter(
            split_length=params["length"],
            split_overlap=params["overlap"],
            split_unit="char",
            separators=params["separators"],
        )
    elif strategy == "semantic":
        splitter = SemanticSplitter(
            models.dense_text_embedder(dense),
            params["breakpoint_percentile"],
            params["min_sentences"],
            params["max_sentences"],
        )
        # embedder is a component, not serializable: primitives only (default_to_dict shape)
        splitter.to_dict = lambda: {
            "type": "rag_worker.components.semantic_splitter.SemanticSplitter",
            "init_parameters": {
                "breakpoint_percentile": params["breakpoint_percentile"],
                "min_sentences": params["min_sentences"],
                "max_sentences": params["max_sentences"],
            },
        }
    elif strategy == "structure":
        splitter = StructureChunker(
            models.tokenizer(dense.model), params["max_tokens"], params["merge_peers"]
        )
        # tokenizer is a tokenizers.Tokenizer, not serializable: primitives only (default_to_dict shape)
        splitter.to_dict = lambda: {
            "type": "rag_worker.components.structure_chunker.StructureChunker",
            "init_parameters": {
                "max_tokens": params["max_tokens"],
                "merge_peers": params["merge_peers"],
            },
        }
    elif strategy == "table":
        splitter = TableChunker(params["row_chunks"], params["text_length"], params["text_overlap"])
    else:
        raise WorkerError("UNSUPPORTED_FOR_STRATEGY", details={"strategy": strategy})

    pipeline = Pipeline()
    pipeline.add_component("splitter", splitter)
    pipeline.add_component("annotator", ChunkAnnotator())
    pipeline.connect("splitter.documents", "annotator.documents")
    return pipeline


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
    source_text = parse_artifact["full_text"]
    elements = parse_artifact["elements"]
    if strategy == "structure":
        if docling_json is None:
            raise WorkerError("UNSUPPORTED_FOR_STRATEGY", details={"parse_strategy": "plain_text"})
        inputs: dict[str, Any] = {
            "docling_json": docling_json,
            "elements": elements,
            "source_text": source_text,
            "file_id": file_id,
        }
    elif strategy == "table":
        inputs = {
            "elements": elements,
            "source_text": source_text,
            "file_id": file_id,
        }
    elif strategy in ("fixed", "sentence", "recursive", "semantic"):
        inputs = {
            "documents": [Document(content=source_text)],
            "elements": elements,
            "source_text": source_text,
            "file_id": file_id,
        }
    else:
        raise WorkerError("UNSUPPORTED_FOR_STRATEGY", details={"strategy": strategy})

    # splitter is mid-pipeline (never a leaf), so ask for its outputs explicitly to read 'semantic'
    out = pipeline.run(inputs, include_outputs_from={"splitter"})
    return {
        "chunks": out["annotator"]["chunks"],
        "semantic": out.get("splitter", {}).get("semantic"),
    }
