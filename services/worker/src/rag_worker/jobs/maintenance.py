"""Utility jobs without callbacks or events (contracts/jobs/drop_collection, delete_points)."""

from typing import Any


async def drop_collection(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Validate JobPayloadDropCollection; asyncio.to_thread(qdrant_admin.drop_collection,
    QdrantClient(url=ctx['qdrant_url']), name) -> {'status': 'done'}. Errors -> log, {'status': 'failed'}."""
    raise NotImplementedError("not implemented")


async def delete_points(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Validate JobPayloadDeletePoints; qdrant_admin.delete_file_points -> {'status': 'done',
    'deleted': n}. Errors -> log, {'status': 'failed'}."""
    raise NotImplementedError("not implemented")
