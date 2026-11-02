"""Unit tests for to_qdrant_filter (rag_api.qdrant_read):
PayloadFilter -> qdrant_client.models.Filter, None when the filter is empty."""

from qdrant_client import models

from rag_api.contracts_gen.shared.common_schema import PayloadFilter
from rag_api.qdrant_read import to_qdrant_filter


def test_empty_payload_filter_returns_none() -> None:
    assert to_qdrant_filter(PayloadFilter()) is None


def test_empty_must_list_returns_none() -> None:
    assert to_qdrant_filter(PayloadFilter(must=[])) is None


def test_must_match_any_maps_to_match_any() -> None:
    flt = PayloadFilter.model_validate({"must": [{"key": "tags", "match": {"any": ["hr"]}}]})
    assert to_qdrant_filter(flt) == models.Filter(
        must=[models.FieldCondition(key="meta.tags", match=models.MatchAny(any=["hr"]))]
    )


def test_must_match_value_maps_to_match_value() -> None:
    flt = PayloadFilter.model_validate({"must": [{"key": "file_id", "match": {"value": "abc"}}]})
    assert to_qdrant_filter(flt) == models.Filter(
        must=[models.FieldCondition(key="meta.file_id", match=models.MatchValue(value="abc"))]
    )


def test_must_range_maps_to_range() -> None:
    flt = PayloadFilter.model_validate({"must": [{"key": "page", "range": {"gte": 1, "lte": 3}}]})
    assert to_qdrant_filter(flt) == models.Filter(
        must=[models.FieldCondition(key="meta.page", range=models.Range(gte=1, lte=3))]
    )


def test_must_range_gte_only_leaves_lte_none() -> None:
    flt = PayloadFilter.model_validate({"must": [{"key": "page", "range": {"gte": 2}}]})
    assert to_qdrant_filter(flt) == models.Filter(
        must=[models.FieldCondition(key="meta.page", range=models.Range(gte=2))]
    )


def test_should_list_maps_to_should() -> None:
    flt = PayloadFilter.model_validate(
        {"should": [{"key": "tags", "match": {"any": ["hr", "q3"]}}]}
    )
    assert to_qdrant_filter(flt) == models.Filter(
        should=[models.FieldCondition(key="meta.tags", match=models.MatchAny(any=["hr", "q3"]))]
    )


def test_must_not_list_maps_to_must_not() -> None:
    flt = PayloadFilter.model_validate(
        {"must_not": [{"key": "file_id", "match": {"value": "abc"}}]}
    )
    assert to_qdrant_filter(flt) == models.Filter(
        must_not=[models.FieldCondition(key="meta.file_id", match=models.MatchValue(value="abc"))]
    )
