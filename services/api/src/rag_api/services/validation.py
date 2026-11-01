from typing import Any


def validate_stage_params(stage: str, params: dict[str, Any]) -> None:
    """Cross-field rules the JSON schema cannot express (api.yaml runChunk) -> VALIDATION_ERROR:
    chunk fixed/sentence/recursive: overlap >= length (details.field='params.overlap');
    chunk table: text_overlap >= text_length ('params.text_overlap');
    chunk semantic: min_sentences > max_sentences ('params.min_sentences').
    Every other stage/params: no-op."""
    raise NotImplementedError("not implemented")
