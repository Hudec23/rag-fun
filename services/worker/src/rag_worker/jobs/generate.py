from typing import Any

from rag_worker.contracts_gen.jobs.generate_schema import JobPayloadGenerate
from rag_worker.report import StageReporter, run_stage


async def generate_body(
    job: JobPayloadGenerate, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/generate.schema.json and the generate summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
    raise NotImplementedError("not implemented")


async def generate(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return await run_stage(ctx, payload, JobPayloadGenerate, generate_body)
