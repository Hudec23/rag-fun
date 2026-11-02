"""Stage run reads, artifact proxy and page images (R-014)."""

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.config import Settings
from rag_api.db.models import StageRunRow
from rag_api.errors import AppError
from rag_api.s3 import ObjectNotFound, ObjectStore
from rag_api.schemas.runs import StageRunList, StageRunOut
from rag_api.services.stages import stage_run_out


async def load_stage_run(session: AsyncSession, stage_run_id: str) -> StageRunRow:
    """404 STAGE_RUN_NOT_FOUND (details.stage_run_id)."""
    row = await session.get(StageRunRow, stage_run_id)
    if row is None:
        raise AppError("STAGE_RUN_NOT_FOUND", details={"stage_run_id": stage_run_id})
    return row


async def get_stage_run(session: AsyncSession, stage_run_id: str) -> StageRunOut:
    """404 STAGE_RUN_NOT_FOUND (details.stage_run_id)."""
    return stage_run_out(await load_stage_run(session, stage_run_id))


async def list_stage_runs(session: AsyncSession, run_id: str, stage: str) -> StageRunList:
    """All versions, version desc. Unknown run -> empty list."""
    rows = (
        await session.scalars(
            select(StageRunRow)
            .where(StageRunRow.run_id == run_id, StageRunRow.stage == stage)
            .order_by(StageRunRow.version.desc())
        )
    ).all()
    return StageRunList(items=[stage_run_out(row) for row in rows])


async def get_artifact(
    session: AsyncSession, store: ObjectStore, settings: Settings, stage_run_id: str
) -> bytes:
    """Raw JSON bytes from bucket artifacts. 404 STAGE_RUN_NOT_FOUND; artifact_key None or object
    missing (ObjectNotFound) -> 404 ARTIFACT_NOT_FOUND (details.stage_run_id)."""
    row = await load_stage_run(session, stage_run_id)
    if row.artifact_key is None:
        raise AppError("ARTIFACT_NOT_FOUND", details={"stage_run_id": stage_run_id})
    try:
        return await store.get_bytes(settings.s3_bucket_artifacts, row.artifact_key)
    except ObjectNotFound as e:
        raise AppError("ARTIFACT_NOT_FOUND", details={"stage_run_id": stage_run_id}) from e


async def get_page_image(
    session: AsyncSession, store: ObjectStore, settings: Settings, stage_run_id: str, page_no: int
) -> bytes:
    """PNG bytes. 404 STAGE_RUN_NOT_FOUND. Not a parse run, no artifact, page_no not in pages, or
    image_key None/missing -> 404 PAGE_NOT_FOUND (details.page_no). Reads the parse artifact JSON
    to find pages[].image_key. Rolls the session back on any AppError, mirroring get_session."""
    try:
        row = await load_stage_run(session, stage_run_id)
        if row.stage != "parse" or row.artifact_key is None:
            raise AppError("PAGE_NOT_FOUND", details={"page_no": page_no})
        try:
            data = await store.get_bytes(settings.s3_bucket_artifacts, row.artifact_key)
        except ObjectNotFound as e:
            raise AppError("PAGE_NOT_FOUND", details={"page_no": page_no}) from e
        artifact = json.loads(data)
        pages: list[dict[str, Any]] = artifact.get("pages", [])
        page = next((p for p in pages if p.get("page_no") == page_no), None)
        image_key = page.get("image_key") if page is not None else None
        if image_key is None:
            raise AppError("PAGE_NOT_FOUND", details={"page_no": page_no})
        try:
            return await store.get_bytes(settings.s3_bucket_artifacts, image_key)
        except ObjectNotFound as e:
            raise AppError("PAGE_NOT_FOUND", details={"page_no": page_no}) from e
    except AppError:
        await session.rollback()
        raise
