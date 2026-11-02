"""Unit tests for the rerank pipeline + artifact (services/worker/src/rag_worker/pipelines/rerank.py):
build_rerank_pipeline wires a single 'ranker' component from ModelSet, and rerank_artifact reshapes
the reranked Documents (or, when disabled, the un-reranked before hits) into the after list of
contracts/artifacts/rerank.schema.json. The module is a stub raising NotImplementedError, so every
test here is red until T-worker-034 lands."""

import dataclasses
import json
from typing import Any

from haystack import Document
from haystack_integrations.document_stores.qdrant.converters import convert_id

from rag_worker.components.hits import hit_to_document
from rag_worker.models.registry import FakeModelSet
from rag_worker.pipelines.rerank import build_rerank_pipeline, rerank_artifact
from tests.conftest import FIXTURES
from tests.contract import errors

RETRIEVE = json.loads((FIXTURES / "artifact_retrieve.json").read_text())
BEFORE: list[dict[str, Any]] = [entry["hit"] for entry in RETRIEVE["fused"]]
D1 = BEFORE[0]  # doc ...:00001, rank 1 in before
D3 = BEFORE[1]  # doc ...:00003, rank 2 in before
MODEL = "Xenova/ms-marco-MiniLM-L-6-v2"
QUERY = "How did revenue change?"


def _reranked() -> list[Document]:
    """Pipeline output: d3 (score 0.9) then d1 (score 0.5) as Documents."""
    return [
        dataclasses.replace(hit_to_document(D3), score=0.9),
        dataclasses.replace(hit_to_document(D1), score=0.5),
    ]


def test_enabled_after_remaps_rank_previous_rank_and_rerank_score() -> None:
    artifact = rerank_artifact(True, MODEL, 2, QUERY, BEFORE, _reranked())
    assert artifact["schema_version"] == 1
    assert artifact["stage"] == "rerank"
    assert artifact["enabled"] is True
    assert artifact["model"] == MODEL
    assert artifact["top_n"] == 2
    assert artifact["query"] == QUERY
    assert artifact["before"] == BEFORE
    after = artifact["after"]
    assert len(after) == 2
    assert after[0]["hit"]["point_id"] == convert_id(D3["doc_id"])
    assert after[0]["hit"]["doc_id"] == D3["doc_id"]
    assert after[0]["hit"]["rank"] == 1
    assert after[0]["hit"]["score"] == 0.9
    assert after[0]["hit"]["content"] == D3["content"]
    assert after[0]["hit"]["meta"] == D3["meta"]
    assert after[0]["previous_rank"] == 2
    assert after[0]["rerank_score"] == 0.9
    assert after[1]["hit"]["point_id"] == convert_id(D1["doc_id"])
    assert after[1]["hit"]["doc_id"] == D1["doc_id"]
    assert after[1]["hit"]["rank"] == 2
    assert after[1]["hit"]["score"] == 0.5
    assert after[1]["hit"]["content"] == D1["content"]
    assert after[1]["hit"]["meta"] == D1["meta"]
    assert after[1]["previous_rank"] == 1
    assert after[1]["rerank_score"] == 0.5
    assert errors(artifact, "artifacts/rerank.schema.json") == []


def test_disabled_after_is_first_top_n_with_null_score_and_model() -> None:
    artifact = rerank_artifact(False, None, 2, QUERY, BEFORE, None)
    assert artifact["enabled"] is False
    assert artifact["model"] is None
    assert artifact["top_n"] == 2
    assert artifact["query"] == QUERY
    assert artifact["before"] == BEFORE
    assert artifact["after"] == [
        {"hit": BEFORE[0], "previous_rank": 1, "rerank_score": None},
        {"hit": BEFORE[1], "previous_rank": 2, "rerank_score": None},
    ]
    assert errors(artifact, "artifacts/rerank.schema.json") == []


def test_artifact_validates_rerank_schema() -> None:
    enabled = rerank_artifact(True, MODEL, 2, QUERY, BEFORE, _reranked())
    assert errors(enabled, "artifacts/rerank.schema.json") == []
    disabled = rerank_artifact(False, None, 3, QUERY, BEFORE, None)
    assert errors(disabled, "artifacts/rerank.schema.json") == []


def test_build_rerank_pipeline_wires_ranker_and_ranks_by_overlap() -> None:
    pipeline = build_rerank_pipeline(MODEL, 2, FakeModelSet())
    assert set(pipeline.to_dict()["components"]) == {"ranker"}
    out = pipeline.run(
        {
            "ranker": {
                "query": "tax refund",
                "documents": [
                    Document(
                        id="019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a01:00001",
                        content="tax bracket changes only",
                    ),
                    Document(
                        id="019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a01:00002",
                        content="tax refund form due soon",
                    ),
                    Document(
                        id="019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a01:00003",
                        content="nothing about money",
                    ),
                ],
            }
        }
    )
    docs = out["ranker"]["documents"]
    assert [doc.id for doc in docs] == [
        "019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a01:00002",
        "019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a01:00001",
    ]
    assert [doc.score for doc in docs] == [0.666667, 0.333333]
