from typing import Any

from rag_worker.contracts_gen.jobs.chunk_schema import JobPayloadChunk
from rag_worker.report import StageReporter, run_stage


async def chunk_body(
    job: JobPayloadChunk, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/chunk.schema.json and the chunk summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
    raise NotImplementedError("not implemented")


async def chunk(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return await run_stage(ctx, payload, JobPayloadChunk, chunk_body)
