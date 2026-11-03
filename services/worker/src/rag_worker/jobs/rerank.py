"""rerank job: read the retrieve artifact, rerank its fused hits with the ranker when params.enabled
(else pass the before order through), store the rerank artifact and report the done/failed stage
result."""

import asyncio
from typing import Any

from rag_worker.components.hits import hit_to_document
from rag_worker.contracts_gen.jobs.rerank_schema import JobPayloadRerank
from rag_worker.pipelines.rerank import build_rerank_pipeline, rerank_artifact
from rag_worker.report import StageReporter, run_stage


async def rerank_body(
    job: JobPayloadRerank, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/rerank.schema.json and the rerank summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
    settings = ctx["settings"]
    store = ctx["store"]
    params = job.params
    ret = await store.get_json(settings.s3_bucket_artifacts, job.retrieve_artifact_key)
    before = [entry["hit"] for entry in ret["fused"]]
    docs: list[Any] | None = None
    if params.enabled:
        pipe = await asyncio.to_thread(
            build_rerank_pipeline, job.model, params.top_n, ctx["models"]
        )
        out = await asyncio.to_thread(
            pipe.run,
            {"ranker": {"query": job.question, "documents": [hit_to_document(h) for h in before]}},
        )
        docs = out["ranker"]["documents"]
    artifact = rerank_artifact(
        params.enabled, job.model or None, params.top_n, job.question, before, docs or None
    )
    summary = {
        "stage": "rerank",
        "enabled": params.enabled,
        "in": len(before),
        "out": len(artifact["after"]),
    }
    return artifact, summary


async def rerank(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return await run_stage(ctx, payload, JobPayloadRerank, rerank_body)
