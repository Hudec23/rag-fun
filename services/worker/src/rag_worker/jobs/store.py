from typing import Any

from rag_worker.contracts_gen.jobs.store_schema import JobPayloadStore
from rag_worker.report import StageReporter, run_stage


async def store_body(
    job: JobPayloadStore, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/store.schema.json and the store summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
    raise NotImplementedError("not implemented")


async def store(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return await run_stage(ctx, payload, JobPayloadStore, store_body)
