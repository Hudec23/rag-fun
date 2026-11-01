from typing import Any

from rag_worker.contracts_gen.jobs.embed_schema import JobPayloadEmbed
from rag_worker.report import StageReporter, run_stage


async def embed_body(
    job: JobPayloadEmbed, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/embed.schema.json and the embed summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
    raise NotImplementedError("not implemented")


async def embed(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return await run_stage(ctx, payload, JobPayloadEmbed, embed_body)
