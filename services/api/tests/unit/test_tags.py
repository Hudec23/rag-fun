"""Unit tests for tag helpers normalize_tags + parse_tags_csv (rag_api.services.tags)."""

import pytest

from rag_api.errors import AppError
from rag_api.services.tags import normalize_tags, parse_tags_csv


def test_normalize_dedupes_and_sorts_ascending() -> None:
    assert normalize_tags(["b", "a", "b"]) == ["a", "b"]


def test_normalize_empty_list() -> None:
    assert normalize_tags([]) == []


def test_parse_csv_splits_strips_lowercases_and_drops_empty() -> None:
    assert parse_tags_csv("finance, q3,,Q3 ") == ["finance", "q3"]


def test_parse_csv_none_and_empty_string() -> None:
    assert parse_tags_csv(None) == []
    assert parse_tags_csv("") == []


def test_parse_csv_invalid_tag_raises_validation_error() -> None:
    with pytest.raises(AppError) as exc:
        parse_tags_csv("ok,Bad Tag!")
    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.details == {"field": "tags"}


def test_parse_csv_tag_longer_than_64_chars_raises() -> None:
    with pytest.raises(AppError) as exc:
        parse_tags_csv("a" * 65)
    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.details == {"field": "tags"}


def test_parse_csv_more_than_32_tags_raises() -> None:
    with pytest.raises(AppError) as exc:
        parse_tags_csv(",".join(f"t{i}" for i in range(33)))
    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.details == {"field": "tags"}


def test_parse_csv_all_allowed_characters() -> None:
    assert parse_tags_csv("v1.2:beta_x-y") == ["v1.2:beta_x-y"]
