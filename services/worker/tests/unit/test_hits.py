"""Unit tests for Hit conversions (services/worker/src/rag_worker/components/hits.py):
to_hit turns a retrieved Haystack Document into a Hit dict per
contracts/shared/common.schema.json#/$defs/Hit, and hit_to_document is its inverse for reranking.
The module is a stub raising NotImplementedError, so every test here is red until T-worker-030 lands."""

import copy
import json
from typing import Any

import pytest
from haystack import Document
from haystack_integrations.document_stores.qdrant.converters import convert_id
from pydantic import ValidationError

from rag_worker.components.hits import hit_to_document, to_hit
from tests.conftest import FIXTURES
from tests.contract import errors

POINT = json.loads((FIXTURES / "qdrant__payload.json").read_text())
DOC_ID = POINT["id"]
META = POINT["meta"]
RAW_SCORE = 0.12345678
ROUNDED_SCORE = 0.123457


def _doc(score: float | None = None, meta: dict[str, Any] | None = None) -> Document:
    return Document(
        id=DOC_ID, content="x", meta=copy.deepcopy(meta if meta is not None else META), score=score
    )


def test_to_hit_maps_point_id_rank_and_score_and_validates_as_hit() -> None:
    hit = to_hit(_doc(RAW_SCORE), 1)
    assert hit["point_id"] == convert_id(DOC_ID)
    assert hit["doc_id"] == DOC_ID
    assert hit["rank"] == 1
    assert hit["score"] == ROUNDED_SCORE
    assert hit["content"] == "x"
    assert hit["meta"] == META
    assert errors(hit, "shared/common.schema.json#/$defs/Hit") == []


def test_explicit_score_wins_over_doc_score_and_missing_score_defaults_zero() -> None:
    assert to_hit(_doc(0.3), 2, score=0.75)["score"] == 0.75
    assert to_hit(_doc(None), 2)["score"] == 0.0


def test_invalid_meta_missing_file_id_raises_validation_error() -> None:
    meta = copy.deepcopy(META)
    del meta["file_id"]
    with pytest.raises(ValidationError):
        to_hit(_doc(RAW_SCORE, meta), 1)


def test_hit_to_document_round_trips_id_content_meta_and_score() -> None:
    hit = to_hit(_doc(RAW_SCORE), 1)
    doc = hit_to_document(hit)
    assert doc.id == DOC_ID
    assert doc.content == "x"
    assert doc.meta == META
    assert doc.score == hit["score"] == ROUNDED_SCORE
