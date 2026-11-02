from typing import Any

from rag_api.errors import AppError

_OVERLAP_STRATEGIES = ("fixed", "sentence", "recursive")


def validate_stage_params(stage: str, params: dict[str, Any]) -> None:
    """Cross-field rules the JSON schema cannot express (api.yaml runChunk) -> VALIDATION_ERROR:
    chunk fixed/sentence/recursive: overlap >= length (details.field='params.overlap');
    chunk table: text_overlap >= text_length ('params.text_overlap');
    chunk semantic: min_sentences > max_sentences ('params.min_sentences').
    Every other stage/params: no-op."""
    if stage != "chunk":
        return
    strategy = params.get("strategy")
    if strategy in _OVERLAP_STRATEGIES:
        length = params.get("length")
        overlap = params.get("overlap")
        if isinstance(length, int) and isinstance(overlap, int) and overlap >= length:
            raise AppError("VALIDATION_ERROR", details={"field": "params.overlap"})
    elif strategy == "table":
        text_length = params.get("text_length")
        text_overlap = params.get("text_overlap")
        if (
            isinstance(text_length, int)
            and isinstance(text_overlap, int)
            and text_overlap >= text_length
        ):
            raise AppError("VALIDATION_ERROR", details={"field": "params.text_overlap"})
    elif strategy == "semantic":
        min_sentences = params.get("min_sentences")
        max_sentences = params.get("max_sentences")
        if (
            isinstance(min_sentences, int)
            and isinstance(max_sentences, int)
            and min_sentences > max_sentences
        ):
            raise AppError("VALIDATION_ERROR", details={"field": "params.min_sentences"})
