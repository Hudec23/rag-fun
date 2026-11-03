"""Utility jobs without callbacks or events (contracts/jobs/drop_collection, delete_points)."""

import asyncio
from typing import Any

import structlog
from pydantic import ValidationError
from qdrant_client import QdrantClient

from rag_worker import qdrant_admin
from rag_worker.contracts_gen.jobs.delete_points_schema import JobPayloadDeletePoints
from rag_worker.contracts_gen.jobs.drop_collection_schema import JobPayloadDropCollection

log = structlog.get_logger()


async def drop_collection(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Validate JobPayloadDropCollection; asyncio.to_thread(qdrant_admin.drop_collection,
    QdrantClient(url=ctx['qdrant_url']), name) -> {'status': 'done'}. Errors -> log, {'status': 'failed'}."""
    try:
        job = JobPayloadDropCollection.model_validate(payload)
    except ValidationError as e:
        log.error("invalid drop_collection payload", error=str(e)[:300])
        return {"status": "failed"}
    try:
        client = QdrantClient(url=ctx["qdrant_url"])
        try:
            await asyncio.to_thread(qdrant_admin.drop_collection, client, job.qdrant_name)
        finally:
            client.close()
    except Exception as e:  # noqa: BLE001
        log.warning("drop_collection failed", error=str(e)[:300])
        return {"status": "failed"}
    return {"status": "done"}


async def delete_points(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Validate JobPayloadDeletePoints; qdrant_admin.delete_file_points -> {'status': 'done',
    'deleted': n}. Errors -> log, {'status': 'failed'}."""
    try:
        job = JobPayloadDeletePoints.model_validate(payload)
    except ValidationError as e:
        log.error("invalid delete_points payload", error=str(e)[:300])
        return {"status": "failed"}
    try:
        client = QdrantClient(url=ctx["qdrant_url"])
        try:
            deleted = await asyncio.to_thread(
                qdrant_admin.delete_file_points, client, job.qdrant_name, job.file_id
            )
        finally:
            client.close()
    except Exception as e:  # noqa: BLE001
        log.warning("delete_points failed", error=str(e)[:300])
        return {"status": "failed"}
    return {"status": "done", "deleted": deleted}
