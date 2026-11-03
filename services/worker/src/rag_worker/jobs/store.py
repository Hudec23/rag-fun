"""store job: read the chunk + embed artifacts, delete the previous points of this file, write all
chunks to the Qdrant collection, store the store artifact and report the done/failed stage result."""

import asyncio
from typing import Any

from haystack_integrations.document_stores.qdrant.converters import convert_id
from qdrant_client import QdrantClient

from rag_worker import qdrant_admin
from rag_worker.contracts_gen.jobs.store_schema import JobPayloadStore
from rag_worker.errors import WorkerError
from rag_worker.ids import to_iso, utcnow
from rag_worker.pipelines.store import build_store_pipeline, documents_for_store
from rag_worker.report import StageReporter, run_stage


async def store_body(
    job: JobPayloadStore, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/store.schema.json and the store summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
    settings = ctx["settings"]
    store = ctx["store"]
    bucket = settings.s3_bucket_artifacts
    chunk = await store.get_json(bucket, job.chunk_artifact_key)
    embed = await store.get_json(bucket, job.embed_artifact_key)
    meta_base = {
        "file_id": job.file.file_id,
        "batch_id": job.file.batch_id,
        "batch_name": job.file.batch_name,
        "filename": job.file.filename,
        "mime": job.file.mime,
        "tags": job.file.tags,
        "ingest_run_id": job.run_id,
        "dense_model": embed["dense_model"],
        "sparse_model": embed["sparse_model"],
        "parse_strategy": job.parse_strategy,
        "chunk_strategy": job.chunk_strategy,
    }
    stored_at = to_iso(utcnow())
    docs = documents_for_store(chunk, embed, meta_base, stored_at)
    point_ids = [convert_id(doc.id) for doc in docs]
    payload_sample = docs[0].to_dict(flatten=False)
    payload_sample.pop("embedding", None)
    payload_sample.pop("sparse_embedding", None)
    qdrant_name = job.collection.qdrant_name
    client = QdrantClient(url=ctx["qdrant_url"])
    try:
        points_deleted = await asyncio.to_thread(
            qdrant_admin.delete_file_points, client, qdrant_name, job.file.file_id
        )
        doc_store = await asyncio.to_thread(
            qdrant_admin.document_store, ctx["qdrant_url"], qdrant_name, job.collection.dense.dims
        )
        pipe = await asyncio.to_thread(build_store_pipeline, doc_store)
        await asyncio.to_thread(pipe.run, {"documents": docs})
    except Exception as e:
        raise WorkerError("QDRANT_ERROR") from e
    finally:
        client.close()
    artifact = {
        "schema_version": 1,
        "stage": "store",
        "qdrant_collection": qdrant_name,
        "points_deleted": points_deleted,
        "points_written": len(docs),
        "point_ids": point_ids,
        "payload_sample": payload_sample,
        "vector_config": {
            "dense_name": "text-dense",
            "dense_size": job.collection.dense.dims,
            "distance": "Cosine",
            "sparse_name": "text-sparse",
            "sparse_modifier": "idf",
        },
    }
    summary = {
        "stage": "store",
        "points_written": len(docs),
        "points_deleted": points_deleted,
        "qdrant_collection": qdrant_name,
    }
    return artifact, summary


async def store(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return await run_stage(ctx, payload, JobPayloadStore, store_body)
