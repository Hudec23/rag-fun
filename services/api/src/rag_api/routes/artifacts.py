from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.config import Settings
from rag_api.db.session import get_session
from rag_api.deps import get_store, settings_dep
from rag_api.s3 import ObjectStore
from rag_api.schemas.base import Id
from rag_api.schemas.runs import Stage, StageRunList, StageRunOut
from rag_api.services import artifacts

router = APIRouter(tags=["artifacts"])


@router.get("/stage-runs", response_model=StageRunList)
async def list_stage_runs(
    run_id: Annotated[Id, Query()],
    stage: Annotated[Stage, Query()],
    session: AsyncSession = Depends(get_session),
) -> StageRunList:
    return await artifacts.list_stage_runs(session, run_id, stage)


@router.get("/stage-runs/{stage_run_id}", response_model=StageRunOut)
async def get_stage_run(
    stage_run_id: Id, session: AsyncSession = Depends(get_session)
) -> StageRunOut:
    return await artifacts.get_stage_run(session, stage_run_id)


@router.get("/stage-runs/{stage_run_id}/artifact")
async def get_artifact(
    stage_run_id: Id,
    session: AsyncSession = Depends(get_session),
    store: ObjectStore = Depends(get_store),
    settings: Settings = Depends(settings_dep),
) -> Response:
    data = await artifacts.get_artifact(session, store, settings, stage_run_id)
    return Response(content=data, media_type="application/json")


@router.get("/stage-runs/{stage_run_id}/pages/{page_no}")
async def get_page(
    stage_run_id: Id,
    page_no: Annotated[int, Path(ge=1)],
    session: AsyncSession = Depends(get_session),
    store: ObjectStore = Depends(get_store),
    settings: Settings = Depends(settings_dep),
) -> Response:
    data = await artifacts.get_page_image(session, store, settings, stage_run_id, page_no)
    return Response(
        content=data,
        media_type="image/png",
        headers={"Cache-Control": "max-age=31536000, immutable"},
    )
