"""Unit tests for the embed job (rag_worker.jobs.embed.embed): read the chunk artifact from the
store, run the embed pipeline in batches of params.batch_size, store the embed artifact and report
the done/failed stage result. The embed job is a stub — every test here is red until T-worker-025."""

import copy
import json
from typing import Any

from rag_worker import keys
from rag_worker.jobs.embed import embed
from rag_worker.viz.stats import chunk_stats
from tests.conftest import FIXTURES
from tests.contract import errors

RUN_ID = "019a4b2c-2000-7c00-9000-000000000002"
STAGE_RUN_ID = "019a4b2c-2100-7c00-9000-000000000003"
VERSION = 1
FILE_ID = "019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a01"
TS = "2026-11-01T18:22:05.123Z"
CHUNK_KEY = keys.artifact_key(RUN_ID, "chunk", VERSION)
ARTIFACT_KEY = keys.artifact_key(RUN_ID, "embed", VERSION)
PAYLOAD = json.loads((FIXTURES / "jobs__embed.json").read_text())
CHUNK = json.loads((FIXTURES / "artifact_chunk.json").read_text())
EMPTY_CHUNK = copy.deepcopy(CHUNK)
EMPTY_CHUNK["chunks"] = []
EMPTY_CHUNK["stats"] = chunk_stats([])


def _payload(params: dict[str, Any] | None = None) -> dict[str, Any]:
    """The jobs__embed fixture with the collection's dense model set to all-minilm/384 (and, when
    given, replaced params); the result must validate against jobs/embed.schema.json."""
    payload = copy.deepcopy(PAYLOAD)
    payload["collection"]["dense"] = {
        "model": "all-minilm",
        "dims": 384,
        "ollama_url": PAYLOAD["collection"]["dense"]["ollama_url"],
    }
    if params is not None:
        payload["params"] = params
    return payload


def _stage_event(event_type: str, **extra: Any) -> dict[str, Any]:
    return {
        "type": event_type,
        "run_id": RUN_ID,
        "stage_run_id": STAGE_RUN_ID,
        "stage": "embed",
        "version": VERSION,
        "ts": TS,
        **extra,
    }


async def _seed_chunk(ctx: dict[str, Any], chunk: dict[str, Any] | None = None) -> None:
    """Store the chunk artifact at the payload's chunk_artifact_key, so the embed job reads exactly
    what the chunk job would have written."""
    if chunk is None:
        chunk = CHUNK
    store = ctx["store"]
    bucket = ctx["settings"].s3_bucket_artifacts
    await store.put_json(bucket, PAYLOAD["chunk_artifact_key"], chunk)


async def _run(
    ctx: dict[str, Any], payload: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    result = await embed(ctx, payload)
    artifact = await ctx["store"].get_json(ctx["settings"].s3_bucket_artifacts, ARTIFACT_KEY)
    return result, artifact


async def test_done_embeds_all_chunks(ctx, frozen_now) -> None:
    payload = _payload()
    assert errors(payload, "jobs/embed.schema.json") == []
    assert payload["chunk_artifact_key"] == CHUNK_KEY

    await _seed_chunk(ctx)
    result, artifact = await _run(ctx, payload)

    assert result["status"] == "done"
    assert errors(artifact, "artifacts/embed.schema.json") == []
    assert len(artifact["chunks"]) == 4
    assert [c["doc_id"] for c in artifact["chunks"]] == [c["doc_id"] for c in CHUNK["chunks"]]
    store = ctx["store"]
    artifacts = ctx["settings"].s3_bucket_artifacts
    assert set(store.objects) == {
        (artifacts, CHUNK_KEY),
        (artifacts, ARTIFACT_KEY),
    }
    assert ctx["api"].started == [(STAGE_RUN_ID, TS)]
    assert ctx["api"].results == [
        {
            "stage_run_id": STAGE_RUN_ID,
            "status": "done",
            "artifact_key": ARTIFACT_KEY,
            "summary": result["summary"],
            "error": None,
            "started_at": TS,
            "finished_at": TS,
        }
    ]
    assert ctx["events"].events == [
        (RUN_ID, _stage_event("stage.started")),
        (
            RUN_ID,
            _stage_event("stage.progress", done=4, total=4, message="embedding 4/4"),
        ),
        (
            RUN_ID,
            _stage_event("stage.completed", artifact_key=ARTIFACT_KEY, summary=result["summary"]),
        ),
    ]
    assert errors(ctx["events"].events[0][1], "events/stage.started.schema.json") == []
    assert errors(ctx["events"].events[2][1], "events/stage.completed.schema.json") == []
    assert ctx["running"] == 0


async def test_summary(ctx, frozen_now) -> None:
    payload = _payload()

    await _seed_chunk(ctx)
    result, artifact = await _run(ctx, payload)

    assert result["status"] == "done"
    summary = result["summary"]
    assert summary["stage"] == "embed"
    assert summary["chunks"] == 4
    assert summary["dense_dims"] == 384
    assert summary["mean_tokens"] > 0
    assert summary["over_limit"] == 0
    assert summary["mean_sparse_nnz"] > 0
    assert len(summary) == 6
    assert errors(summary, "shared/summary.schema.json#/$defs/EmbedSummary") == []
    assert ctx["api"].started == [(STAGE_RUN_ID, TS)]
    assert ctx["api"].results == [
        {
            "stage_run_id": STAGE_RUN_ID,
            "status": "done",
            "artifact_key": ARTIFACT_KEY,
            "summary": summary,
            "error": None,
            "started_at": TS,
            "finished_at": TS,
        }
    ]
    assert ctx["running"] == 0


async def test_progress_events_per_batch(ctx, frozen_now) -> None:
    payload = _payload(params={"batch_size": 2})
    assert errors(payload, "jobs/embed.schema.json") == []

    await _seed_chunk(ctx)
    result, artifact = await _run(ctx, payload)

    assert result["status"] == "done"
    assert len(artifact["chunks"]) == 4
    assert ctx["events"].events == [
        (RUN_ID, _stage_event("stage.started")),
        (RUN_ID, _stage_event("stage.progress", done=2, total=4, message="embedding 2/4")),
        (RUN_ID, _stage_event("stage.progress", done=4, total=4, message="embedding 4/4")),
        (
            RUN_ID,
            _stage_event("stage.completed", artifact_key=ARTIFACT_KEY, summary=result["summary"]),
        ),
    ]
    assert errors(ctx["events"].events[1][1], "events/stage.progress.schema.json") == []
    assert errors(ctx["events"].events[2][1], "events/stage.progress.schema.json") == []
    assert ctx["running"] == 0


async def test_empty_chunk_list(ctx, frozen_now) -> None:
    payload = _payload()

    await _seed_chunk(ctx, EMPTY_CHUNK)
    result, artifact = await _run(ctx, payload)

    assert result["status"] == "done"
    assert errors(artifact, "artifacts/embed.schema.json") == []
    assert artifact["chunks"] == []
    assert artifact["similarity"] == []
    assert result["summary"] == {
        "stage": "embed",
        "chunks": 0,
        "dense_dims": 384,
        "mean_tokens": 0,
        "over_limit": 0,
        "mean_sparse_nnz": 0,
    }
    assert ctx["events"].events == [
        (RUN_ID, _stage_event("stage.started")),
        (
            RUN_ID,
            _stage_event("stage.completed", artifact_key=ARTIFACT_KEY, summary=result["summary"]),
        ),
    ]
    assert ctx["running"] == 0
