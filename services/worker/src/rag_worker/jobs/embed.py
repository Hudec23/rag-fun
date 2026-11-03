"""embed job: read the chunk artifact from the store, run the embed pipeline in batches of
params.batch_size, store the embed artifact and report the done/failed stage result."""

import asyncio
from typing import Any

from haystack import Document

from rag_worker.contracts_gen.jobs.embed_schema import JobPayloadEmbed
from rag_worker.errors import WorkerError
from rag_worker.models.registry import TOKENIZERS
from rag_worker.pipelines.embed import build_embed_pipeline, embed_artifact
from rag_worker.report import StageReporter, run_stage


async def embed_body(
    job: JobPayloadEmbed, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/embed.schema.json and the embed summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
    settings = ctx["settings"]
    store = ctx["store"]
    entry = TOKENIZERS.get(job.collection.dense.model)
    if entry is None:
        raise WorkerError("MODEL_NOT_AVAILABLE", details={"model": job.collection.dense.model})
    repo, max_tokens = entry
    chunk = await store.get_json(settings.s3_bucket_artifacts, job.chunk_artifact_key)
    docs = [
        Document(id=c["doc_id"], content=c["text"], meta={"doc_id": c["doc_id"]})
        for c in chunk["chunks"]
    ]
    pipe = await asyncio.to_thread(
        build_embed_pipeline, job.collection, job.params.batch_size, ctx["models"]
    )
    total = len(docs)
    embedded: list[Any] = []
    for start in range(0, total, job.params.batch_size):
        batch = docs[start : start + job.params.batch_size]
        out = await asyncio.to_thread(pipe.run, {"documents": batch})
        embedded.extend(out["tokens"]["documents"])
        await rep.progress(len(embedded), total, f"embedding {len(embedded)}/{total}")
    art = await asyncio.to_thread(embed_artifact, embedded, job.collection, repo, max_tokens)
    chunks = art["chunks"]
    n = len(chunks)
    summary = {
        "stage": "embed",
        "chunks": n,
        "dense_dims": job.collection.dense.dims,
        "mean_tokens": round(sum(c["token_count"] for c in chunks) / n, 2) if n else 0,
        "over_limit": sum(1 for c in chunks if c["over_limit"]),
        "mean_sparse_nnz": (
            round(sum(len(c["sparse"]["indices"]) for c in chunks) / n, 2) if n else 0
        ),
    }
    return art, summary


async def embed(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return await run_stage(ctx, payload, JobPayloadEmbed, embed_body)
