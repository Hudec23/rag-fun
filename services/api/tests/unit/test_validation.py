"""Unit tests for validate_stage_params cross-field rules (rag_api.services.validation)."""

import pytest

from rag_api.errors import AppError
from rag_api.services.validation import validate_stage_params


def test_chunk_fixed_overlap_below_length_returns_none() -> None:
    assert validate_stage_params("chunk", {"strategy": "fixed", "length": 10, "overlap": 9}) is None


def test_chunk_fixed_overlap_equal_to_length_is_validation_error() -> None:
    with pytest.raises(AppError) as exc:
        validate_stage_params("chunk", {"strategy": "fixed", "length": 10, "overlap": 10})
    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.details == {"field": "params.overlap"}


def test_chunk_sentence_overlap_above_length_is_validation_error() -> None:
    with pytest.raises(AppError) as exc:
        validate_stage_params("chunk", {"strategy": "sentence", "length": 2, "overlap": 3})
    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.details == {"field": "params.overlap"}


def test_chunk_recursive_overlap_equal_to_length_is_validation_error() -> None:
    with pytest.raises(AppError) as exc:
        validate_stage_params("chunk", {"strategy": "recursive", "length": 100, "overlap": 100})
    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.details == {"field": "params.overlap"}


def test_chunk_table_text_overlap_equal_to_text_length_is_validation_error() -> None:
    with pytest.raises(AppError) as exc:
        validate_stage_params("chunk", {"strategy": "table", "text_length": 50, "text_overlap": 50})
    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.details == {"field": "params.text_overlap"}


def test_chunk_semantic_min_above_max_is_validation_error_equal_is_ok() -> None:
    with pytest.raises(AppError) as exc:
        validate_stage_params(
            "chunk", {"strategy": "semantic", "min_sentences": 5, "max_sentences": 4}
        )
    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.details == {"field": "params.min_sentences"}
    assert (
        validate_stage_params(
            "chunk", {"strategy": "semantic", "min_sentences": 4, "max_sentences": 4}
        )
        is None
    )


def test_chunk_structure_params_is_ok() -> None:
    assert (
        validate_stage_params(
            "chunk", {"strategy": "structure", "max_tokens": 64, "merge_peers": True}
        )
        is None
    )


def test_parse_and_embed_stages_ignore_params() -> None:
    assert validate_stage_params("parse", {"anything": "at all"}) is None
    assert validate_stage_params("embed", {"batch_size": 16}) is None
