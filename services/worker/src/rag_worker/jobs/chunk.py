"""chunk job: read the parse artifact from the store, run the chunk pipeline for the payload's
strategy, store the chunk artifact and report the done/failed stage result."""

import asyncio
from typing import Any

from rag_worker.contracts_gen.jobs.chunk_schema import JobPayloadChunk
from rag_worker.pipelines.chunk import build_chunk_pipeline, run_chunk
from rag_worker.report import StageReporter, run_stage
from rag_worker.viz.stats import chunk_stats


async def chunk_body(
    job: JobPayloadChunk, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/chunk.schema.json and the chunk summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
    settings = ctx["settings"]
    store = ctx["store"]
    parse = await store.get_json(settings.s3_bucket_artifacts, job.parse_artifact_key)
    docling_key = parse["docling_json_key"]
    docling_json = (
        (await store.get_bytes(settings.s3_bucket_artifacts, docling_key)).decode("utf-8")
        if docling_key is not None
        else None
    )
    strategy = job.params.strategy
    params = job.params.model_dump()
    pipe = await asyncio.to_thread(build_chunk_pipeline, strategy, params, ctx["models"], job.dense)
    out = await asyncio.to_thread(run_chunk, pipe, strategy, parse, docling_json, job.file.file_id)
    stats = chunk_stats([c["char_count"] for c in out["chunks"]])
    artifact = {
        "schema_version": 1,
        "stage": "chunk",
        "strategy": strategy,
        "params": params,
        "parse_strategy": parse["strategy"],
        "source_text": parse["full_text"],
        "chunks": out["chunks"],
        "stats": stats,
        "semantic": out["semantic"],
    }
    summary = {
        "stage": "chunk",
        "chunks": stats["count"],
        "min_chars": stats["min_chars"],
        "max_chars": stats["max_chars"],
        "mean_chars": stats["mean_chars"],
    }
    return artifact, summary


async def chunk(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return await run_stage(ctx, payload, JobPayloadChunk, chunk_body)
