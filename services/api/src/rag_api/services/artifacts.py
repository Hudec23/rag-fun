from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.config import Settings
from rag_api.s3 import ObjectStore
from rag_api.schemas.runs import StageRunList, StageRunOut


async def get_stage_run(session: AsyncSession, stage_run_id: str) -> StageRunOut:
    """404 STAGE_RUN_NOT_FOUND (details.stage_run_id)."""
    raise NotImplementedError("not implemented")


async def list_stage_runs(session: AsyncSession, run_id: str, stage: str) -> StageRunList:
    """All versions, version desc. Unknown run -> empty list."""
    raise NotImplementedError("not implemented")


async def get_artifact(
    session: AsyncSession, store: ObjectStore, settings: Settings, stage_run_id: str
) -> bytes:
    """Raw JSON bytes from bucket artifacts. 404 STAGE_RUN_NOT_FOUND; artifact_key None or object
    missing (ObjectNotFound) -> 404 ARTIFACT_NOT_FOUND (details.stage_run_id)."""
    raise NotImplementedError("not implemented")


async def get_page_image(
    session: AsyncSession, store: ObjectStore, settings: Settings, stage_run_id: str, page_no: int
) -> bytes:
    """PNG bytes. 404 STAGE_RUN_NOT_FOUND. Not a parse run, no artifact, page_no not in pages, or
    image_key None/missing -> 404 PAGE_NOT_FOUND (details.page_no). Reads the parse artifact JSON
    to find pages[].image_key."""
    raise NotImplementedError("not implemented")
