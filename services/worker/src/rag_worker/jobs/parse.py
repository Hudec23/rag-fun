from typing import Any

from rag_worker.contracts_gen.jobs.parse_schema import JobPayloadParse
from rag_worker.report import StageReporter, run_stage


async def parse_body(
    job: JobPayloadParse, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/parse.schema.json and the parse summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
    raise NotImplementedError("not implemented")


async def parse(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return await run_stage(ctx, payload, JobPayloadParse, parse_body)
