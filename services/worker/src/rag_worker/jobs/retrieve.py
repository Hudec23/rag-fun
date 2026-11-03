"""retrieve job: read the transform artifact (or fall back to the question), run the configured
retrieval over the Qdrant collection and report the done/failed stage result."""

import asyncio
from typing import Any

from rag_worker.components.hits import to_hit
from rag_worker.components.rrf import rrf_fuse
from rag_worker.contracts_gen.jobs.retrieve_schema import JobPayloadRetrieve
from rag_worker.pipelines.retrieve import build_retrieve_pipeline, run_retrieve, to_haystack_filters
from rag_worker.qdrant_admin import document_store
from rag_worker.report import StageReporter, run_stage


async def retrieve_body(
    job: JobPayloadRetrieve, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/retrieve.schema.json and the retrieve summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
    settings = ctx["settings"]
    store = ctx["store"]
    params = job.params
    if job.transform_artifact_key is not None:
        transform = await store.get_json(settings.s3_bucket_artifacts, job.transform_artifact_key)
        queries: list[str] = list(transform["queries"])
    else:
        queries = [job.question]
    mode = params.mode
    top_k = params.top_k
    rrf_k = params.rrf_k
    collection = job.collection
    ds = await asyncio.to_thread(
        document_store, ctx["qdrant_url"], collection.qdrant_name, collection.dense.dims
    )
    pipe = await asyncio.to_thread(
        build_retrieve_pipeline, mode, collection, ds, top_k, ctx["models"]
    )
    per = await asyncio.to_thread(
        run_retrieve, pipe, mode, queries, to_haystack_filters(params.filters)
    )
    per_query = [
        {
            "query": entry["query"],
            "dense": [to_hit(doc, rank) for rank, doc in enumerate(entry["dense"], start=1)]
            if entry["dense"] is not None
            else None,
            "sparse": [to_hit(doc, rank) for rank, doc in enumerate(entry["sparse"], start=1)]
            if entry["sparse"] is not None
            else None,
        }
        for entry in per
    ]
    lists = [
        (qi, name, entry[name])
        for qi, entry in enumerate(per)
        for name in ("dense", "sparse")
        if entry[name] is not None
    ]
    if len(queries) == 1 and mode in ("dense", "sparse"):
        fused = [
            {"hit": hit, "source_ranks": [{"query_index": 0, "list": mode, "rank": rank}]}
            for rank, hit in enumerate(per_query[0][mode], start=1)
        ]
    else:
        fused = [
            {
                "hit": to_hit(fused_entry["doc"], rank, fused_entry["score"]),
                "source_ranks": fused_entry["source_ranks"],
            }
            for rank, fused_entry in enumerate(rrf_fuse(lists, rrf_k, top_k), start=1)
        ]
    artifact = {
        "schema_version": 1,
        "stage": "retrieve",
        "mode": mode,
        "top_k": top_k,
        "rrf_k": rrf_k,
        "filters": params.filters.model_dump(mode="json", exclude_none=True),
        "per_query": per_query,
        "fused": fused,
    }
    summary = {"stage": "retrieve", "queries": len(queries), "hits": len(fused)}
    return artifact, summary


async def retrieve(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return await run_stage(ctx, payload, JobPayloadRetrieve, retrieve_body)
