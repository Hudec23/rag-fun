from typing import Any

from rag_worker.contracts_gen.jobs.retrieve_schema import JobPayloadRetrieve
from rag_worker.report import StageReporter, run_stage


async def retrieve_body(
    job: JobPayloadRetrieve, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/retrieve.schema.json and the retrieve summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
    raise NotImplementedError("not implemented")


async def retrieve(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return await run_stage(ctx, payload, JobPayloadRetrieve, retrieve_body)
