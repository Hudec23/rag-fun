import asyncio
from typing import Any

from rag_worker.contracts_gen.jobs.transform_schema import JobPayloadTransform
from rag_worker.errors import WorkerError
from rag_worker.pipelines.transform import build_transform_pipeline, transform_artifact
from rag_worker.report import StageReporter, run_stage


async def transform_body(
    job: JobPayloadTransform, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/transform.schema.json and the transform summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
    params = job.params
    if params.strategy == "none":
        artifact = transform_artifact(
            params.strategy, job.question, None, [], None, params.num_queries
        )
    else:
        pipe = await asyncio.to_thread(
            build_transform_pipeline, params.strategy, job.chat, ctx["models"]
        )
        prompt_vars: dict[str, Any] = {"question": job.question}
        if params.strategy == "multi_query":
            prompt_vars["n"] = params.num_queries
        try:
            res = await asyncio.to_thread(pipe.run, {"prompt": prompt_vars})
        except Exception as e:
            raise WorkerError("LLM_ERROR", details={"reason": str(e.__cause__ or e)[:300]}) from e
        reply = res["llm"]["replies"][0].text
        messages = [{"role": m.role.value, "content": m.text} for m in res["prompt"]]
        artifact = transform_artifact(
            params.strategy, job.question, reply, messages, job.chat, params.num_queries
        )
    summary = {"stage": "transform", "queries": len(artifact["queries"])}
    return artifact, summary


async def transform(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return await run_stage(ctx, payload, JobPayloadTransform, transform_body)
