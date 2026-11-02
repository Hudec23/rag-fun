"""Store job (rag_worker.jobs.store.store): read the chunk + embed artifacts, delete the previous
points of this file, write all chunks to the Qdrant collection and report the stage result.
Real Qdrant via qdrant-test (QDRANT_URL). The store job is a stub — every test here is red until
T-worker-027."""

import copy
import json
from collections.abc import Iterator
from contextlib import suppress
from typing import Any
from uuid import uuid4

import pytest
from haystack_integrations.document_stores.qdrant.converters import convert_id
from qdrant_client import QdrantClient

from rag_worker import keys
from rag_worker.jobs.store import store
from tests.conftest import FIXTURES
from tests.contract import errors

RUN_ID = "019a4b2c-2000-7c00-9000-000000000002"
STAGE_RUN_ID = "019a4b2c-2100-7c00-9000-000000000003"
VERSION = 1
TS = "2026-11-01T18:22:05.123Z"
ARTIFACT_KEY = keys.artifact_key(RUN_ID, "store", VERSION)
PAYLOAD = json.loads((FIXTURES / "jobs__store.json").read_text())
CHUNK = json.loads((FIXTURES / "artifact_chunk.json").read_text())
ARTIFACT_STORE = json.loads((FIXTURES / "artifact_store.json").read_text())
EXPECTED_POINT_IDS = [convert_id(chunk["doc_id"]) for chunk in CHUNK["chunks"]]
EXPECTED_PAYLOAD_SAMPLE = ARTIFACT_STORE["payload_sample"]
EXPECTED_VECTOR_CONFIG = ARTIFACT_STORE["vector_config"]


def _event(event_type: str, **extra: Any) -> dict[str, Any]:
    return {
        "type": event_type,
        "run_id": RUN_ID,
        "stage_run_id": STAGE_RUN_ID,
        "stage": "store",
        "version": VERSION,
        "ts": TS,
        **extra,
    }


def _summary(name: str, points_deleted: int = 0) -> dict[str, Any]:
    return {
        "stage": "store",
        "points_written": 4,
        "points_deleted": points_deleted,
        "qdrant_collection": name,
    }


def _artifact(name: str, points_deleted: int = 0) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "stage": "store",
        "qdrant_collection": name,
        "points_deleted": points_deleted,
        "points_written": 4,
        "point_ids": EXPECTED_POINT_IDS,
        "payload_sample": EXPECTED_PAYLOAD_SAMPLE,
        "vector_config": EXPECTED_VECTOR_CONFIG,
    }


def _seed(ctx: dict[str, Any], name: str) -> dict[str, Any]:
    """Seed the chunk + embed artifacts and point the payload at a fresh collection (384 dims)."""
    payload = copy.deepcopy(PAYLOAD)
    payload["collection"]["qdrant_name"] = name
    payload["collection"]["dense"]["dims"] = 384
    artifacts = ctx["settings"].s3_bucket_artifacts
    ctx["store"].objects[(artifacts, payload["chunk_artifact_key"])] = (
        FIXTURES / "artifact_chunk.json"
    ).read_bytes()
    ctx["store"].objects[(artifacts, payload["embed_artifact_key"])] = (
        FIXTURES / "artifact_embed.json"
    ).read_bytes()
    return payload


@pytest.fixture
def qdrant(ctx: dict[str, Any]) -> Iterator[tuple[QdrantClient, str]]:
    """(client, fresh collection name) against qdrant-test; the collection is dropped in teardown."""
    client = QdrantClient(url=ctx["qdrant_url"])
    name = "rf_" + uuid4().hex
    yield client, name
    with suppress(Exception):
        client.delete_collection(name)
    client.close()


async def test_store_done_writes_points_and_valid_artifact(ctx, frozen_now, qdrant) -> None:
    assert errors(PAYLOAD, "jobs/store.schema.json") == []
    client, name = qdrant
    payload = _seed(ctx, name)

    result = await store(ctx, payload)

    assert result == {"status": "done", "summary": _summary(name)}
    artifacts = ctx["settings"].s3_bucket_artifacts
    assert set(ctx["store"].objects) == {
        (artifacts, payload["chunk_artifact_key"]),
        (artifacts, payload["embed_artifact_key"]),
        (artifacts, ARTIFACT_KEY),
    }
    assert ctx["api"].started == [(STAGE_RUN_ID, TS)]
    assert ctx["api"].results == [
        {
            "stage_run_id": STAGE_RUN_ID,
            "status": "done",
            "artifact_key": ARTIFACT_KEY,
            "summary": _summary(name),
            "error": None,
            "started_at": TS,
            "finished_at": TS,
        }
    ]
    artifact = await ctx["store"].get_json(artifacts, ARTIFACT_KEY)
    assert artifact == _artifact(name)
    assert errors(artifact, "artifacts/store.schema.json") == []
    assert errors(_summary(name), "shared/summary.schema.json#/$defs/StoreSummary") == []
    assert client.collection_exists(name)
    assert client.count(name).count == 4
    assert ctx["events"].events == [
        (RUN_ID, _event("stage.started")),
        (RUN_ID, _event("stage.completed", artifact_key=ARTIFACT_KEY, summary=_summary(name))),
    ]
    assert errors(ctx["events"].events[0][1], "events/stage.started.schema.json") == []
    assert errors(ctx["events"].events[1][1], "events/stage.completed.schema.json") == []
    assert ctx["running"] == 0


async def test_point_ids_and_payload_sample_match_chunk_order(ctx, frozen_now, qdrant) -> None:
    client, name = qdrant
    payload = _seed(ctx, name)

    result = await store(ctx, payload)

    assert result["status"] == "done"
    artifact = await ctx["store"].get_json(ctx["settings"].s3_bucket_artifacts, ARTIFACT_KEY)
    assert artifact["point_ids"] == EXPECTED_POINT_IDS
    assert len(artifact["point_ids"]) == 4
    assert errors(artifact["payload_sample"], "qdrant/payload.schema.json") == []
    assert artifact["payload_sample"] == EXPECTED_PAYLOAD_SAMPLE
    assert artifact["payload_sample"]["meta"]["tags"] == ["finance", "q3"]
    assert artifact["payload_sample"]["meta"]["tags"] == PAYLOAD["file"]["tags"]
    retrieved = client.retrieve(name, ids=EXPECTED_POINT_IDS)
    assert set(retrieved.ids) == set(EXPECTED_POINT_IDS)
    assert ctx["running"] == 0


async def test_running_store_twice_deletes_previous_points(ctx, frozen_now, qdrant) -> None:
    client, name = qdrant
    payload = _seed(ctx, name)

    first = await store(ctx, payload)
    second = await store(ctx, payload)

    assert first == {"status": "done", "summary": _summary(name)}
    assert second == {"status": "done", "summary": _summary(name, points_deleted=4)}
    assert ctx["api"].results[-1] == {
        "stage_run_id": STAGE_RUN_ID,
        "status": "done",
        "artifact_key": ARTIFACT_KEY,
        "summary": _summary(name, points_deleted=4),
        "error": None,
        "started_at": TS,
        "finished_at": TS,
    }
    artifact = await ctx["store"].get_json(ctx["settings"].s3_bucket_artifacts, ARTIFACT_KEY)
    assert artifact == _artifact(name, points_deleted=4)
    assert errors(artifact, "artifacts/store.schema.json") == []
    assert client.count(name).count == 4
    assert ctx["running"] == 0


async def test_summary_reports_points_written_and_deleted(ctx, frozen_now, qdrant) -> None:
    client, name = qdrant
    payload = _seed(ctx, name)

    result = await store(ctx, payload)

    assert result == {
        "status": "done",
        "summary": {
            "stage": "store",
            "points_written": 4,
            "points_deleted": 0,
            "qdrant_collection": name,
        },
    }
    assert errors(result["summary"], "shared/summary.schema.json#/$defs/StoreSummary") == []
    assert client.count(name).count == 4
    assert ctx["running"] == 0


async def test_unreachable_qdrant_fails_with_qdrant_error(ctx, frozen_now, qdrant) -> None:
    _, name = qdrant
    payload = _seed(ctx, name)
    ctx["qdrant_url"] = "http://127.0.0.1:1"

    result = await store(ctx, payload)

    assert result == {"status": "failed", "code": "QDRANT_ERROR"}
    assert ctx["api"].started == [(STAGE_RUN_ID, TS)]
    [stage_result] = ctx["api"].results
    assert stage_result["stage_run_id"] == STAGE_RUN_ID
    assert stage_result["status"] == "failed"
    assert stage_result["artifact_key"] is None
    assert stage_result["summary"] is None
    assert stage_result["started_at"] == TS
    assert stage_result["finished_at"] == TS
    assert stage_result["error"]["code"] == "QDRANT_ERROR"
    assert stage_result["error"]["message"] == "Qdrant request failed"
    artifacts = ctx["settings"].s3_bucket_artifacts
    assert set(ctx["store"].objects) == {
        (artifacts, payload["chunk_artifact_key"]),
        (artifacts, payload["embed_artifact_key"]),
    }
    events = ctx["events"].events
    assert len(events) == 2
    assert events[0] == (RUN_ID, _event("stage.started"))
    assert events[1][0] == RUN_ID
    assert events[1][1]["type"] == "stage.failed"
    assert events[1][1]["error"]["code"] == "QDRANT_ERROR"
    assert errors(events[1][1], "events/stage.failed.schema.json") == []
    assert ctx["running"] == 0
