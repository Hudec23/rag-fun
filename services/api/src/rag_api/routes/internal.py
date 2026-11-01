"""contracts/openapi/internal.yaml — worker callbacks, guarded by X-Internal-Token."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Path, Response
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.config import Settings
from rag_api.db.session import get_session
from rag_api.deps import get_events, get_queue, settings_dep
from rag_api.errors import AppError
from rag_api.events import EventBus
from rag_api.queue import JobQueue
from rag_api.schemas.runs import Stage
from rag_api.schemas.system import StageResult, StageStarted
from rag_api.services import pipeline_graphs, results


def require_token(
    x_internal_token: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(settings_dep),
) -> None:
    if x_internal_token != settings.internal_token:
        raise AppError("UNAUTHORIZED")


router = APIRouter(prefix="/internal/v1", tags=["internal"], dependencies=[Depends(require_token)])


@router.post("/stage-started", status_code=204)
async def stage_started(
    body: StageStarted, session: AsyncSession = Depends(get_session)
) -> Response:
    await results.record_started(session, body)
    return Response(status_code=204)


@router.post("/stage-results", status_code=204)
async def stage_results(
    body: StageResult,
    session: AsyncSession = Depends(get_session),
    queue: JobQueue = Depends(get_queue),
    events: EventBus = Depends(get_events),
) -> Response:
    await results.record_result(session, queue, events, body)
    return Response(status_code=204)


@router.put("/pipeline-graphs/{stage}/{variant}", status_code=204)
async def put_pipeline_graph(
    stage: Stage,
    variant: Annotated[str, Path(pattern=r"^[a-z_]{1,40}$")],
    body: dict[str, Any],
    session: AsyncSession = Depends(get_session),
) -> Response:
    await pipeline_graphs.put_graph(session, stage, variant, body)
    return Response(status_code=204)
