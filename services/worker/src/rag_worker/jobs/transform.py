from typing import Any

from rag_worker.contracts_gen.jobs.transform_schema import JobPayloadTransform
from rag_worker.report import StageReporter, run_stage


async def transform_body(
    job: JobPayloadTransform, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/transform.schema.json and the transform summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
    raise NotImplementedError("not implemented")


async def transform(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return await run_stage(ctx, payload, JobPayloadTransform, transform_body)
