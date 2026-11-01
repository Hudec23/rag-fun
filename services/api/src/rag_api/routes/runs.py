"""Ingest + query runs and their per-stage endpoints (R-013, R-015..R-018)."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.session import get_session
from rag_api.deps import get_events, get_queue
from rag_api.events import EventBus
from rag_api.queue import JobQueue
from rag_api.schemas.base import Id
from rag_api.schemas.runs import (
    ChunkStageRequest,
    EmbedStageRequest,
    GenerateStageRequest,
    IngestRunAllRequest,
    IngestRunCreate,
    IngestRunOut,
    IngestRunPage,
    ParseStageRequest,
    QueryRunAllRequest,
    QueryRunCreate,
    QueryRunOut,
    QueryRunPage,
    RerankStageRequest,
    RetrieveStageRequest,
    StageRunOut,
    StoreStageRequest,
    TransformStageRequest,
)
from rag_api.services import ingest_runs, query_runs, run_all, stages
from rag_api.services.validation import validate_stage_params

router = APIRouter(tags=["runs"])

Limit = Annotated[int, Query(ge=1, le=200)]
Offset = Annotated[int, Query(ge=0)]


def _params(body: BaseModel) -> dict[str, Any]:
    dumped: dict[str, Any] = body.model_dump(mode="json")["params"]
    return dumped


# ---------------------------------------------------------------- ingest runs


@router.get("/ingest-runs", response_model=IngestRunPage)
async def list_ingest_runs(
    limit: Limit = 50,
    offset: Offset = 0,
    file_id: Id | None = None,
    collection_id: Id | None = None,
    session: AsyncSession = Depends(get_session),
) -> IngestRunPage:
    return await ingest_runs.list_ingest_runs(session, limit, offset, file_id, collection_id)


@router.post("/ingest-runs", response_model=IngestRunOut, status_code=201)
async def create_ingest_run(
    body: IngestRunCreate, session: AsyncSession = Depends(get_session)
) -> IngestRunOut:
    return await ingest_runs.create_ingest_run(session, body)


@router.get("/ingest-runs/{run_id}", response_model=IngestRunOut)
async def get_ingest_run(run_id: Id, session: AsyncSession = Depends(get_session)) -> IngestRunOut:
    return await ingest_runs.ingest_run_out(session, run_id)


async def _start_ingest(
    session: AsyncSession,
    queue: JobQueue,
    events: EventBus,
    run_id: str,
    stage: str,
    body: BaseModel,
) -> StageRunOut:
    run = await ingest_runs.load_ingest_run(session, run_id)
    params = _params(body)
    validate_stage_params(stage, params)
    row = await stages.start_stage(session, queue, events, run, stage, params)
    return stages.stage_run_out(row)


@router.post("/ingest-runs/{run_id}/stages/parse", response_model=StageRunOut, status_code=202)
async def run_parse(
    run_id: Id,
    body: ParseStageRequest,
    session: AsyncSession = Depends(get_session),
    queue: JobQueue = Depends(get_queue),
    events: EventBus = Depends(get_events),
) -> StageRunOut:
    return await _start_ingest(session, queue, events, run_id, "parse", body)


@router.post("/ingest-runs/{run_id}/stages/chunk", response_model=StageRunOut, status_code=202)
async def run_chunk(
    run_id: Id,
    body: ChunkStageRequest,
    session: AsyncSession = Depends(get_session),
    queue: JobQueue = Depends(get_queue),
    events: EventBus = Depends(get_events),
) -> StageRunOut:
    return await _start_ingest(session, queue, events, run_id, "chunk", body)


@router.post("/ingest-runs/{run_id}/stages/embed", response_model=StageRunOut, status_code=202)
async def run_embed(
    run_id: Id,
    body: EmbedStageRequest,
    session: AsyncSession = Depends(get_session),
    queue: JobQueue = Depends(get_queue),
    events: EventBus = Depends(get_events),
) -> StageRunOut:
    return await _start_ingest(session, queue, events, run_id, "embed", body)


@router.post("/ingest-runs/{run_id}/stages/store", response_model=StageRunOut, status_code=202)
async def run_store(
    run_id: Id,
    body: StoreStageRequest,
    session: AsyncSession = Depends(get_session),
    queue: JobQueue = Depends(get_queue),
    events: EventBus = Depends(get_events),
) -> StageRunOut:
    return await _start_ingest(session, queue, events, run_id, "store", body)


@router.post("/ingest-runs/{run_id}/run-all", response_model=IngestRunOut)
async def run_all_ingest(
    run_id: Id,
    body: IngestRunAllRequest,
    session: AsyncSession = Depends(get_session),
    queue: JobQueue = Depends(get_queue),
    events: EventBus = Depends(get_events),
) -> JSONResponse:
    run = await ingest_runs.load_ingest_run(session, run_id)
    params = body.params.model_dump(mode="json")
    for stage, p in params.items():
        validate_stage_params(stage, p)
    queued = await run_all.start_run_all(session, queue, events, run, body.from_stage, params)
    out = await ingest_runs.ingest_run_out(session, run_id)
    return JSONResponse(status_code=202 if queued else 200, content=out.model_dump(mode="json"))


# ---------------------------------------------------------------- query runs


@router.get("/query-runs", response_model=QueryRunPage)
async def list_query_runs(
    limit: Limit = 50,
    offset: Offset = 0,
    collection_id: Id | None = None,
    session: AsyncSession = Depends(get_session),
) -> QueryRunPage:
    return await query_runs.list_query_runs(session, limit, offset, collection_id)


@router.post("/query-runs", response_model=QueryRunOut, status_code=201)
async def create_query_run(
    body: QueryRunCreate, session: AsyncSession = Depends(get_session)
) -> QueryRunOut:
    return await query_runs.create_query_run(session, body)


@router.get("/query-runs/{run_id}", response_model=QueryRunOut)
async def get_query_run(run_id: Id, session: AsyncSession = Depends(get_session)) -> QueryRunOut:
    return await query_runs.query_run_out(session, run_id)


async def _start_query(
    session: AsyncSession,
    queue: JobQueue,
    events: EventBus,
    run_id: str,
    stage: str,
    body: BaseModel,
) -> StageRunOut:
    run = await query_runs.load_query_run(session, run_id)
    row = await stages.start_stage(session, queue, events, run, stage, _params(body))
    return stages.stage_run_out(row)


@router.post("/query-runs/{run_id}/stages/transform", response_model=StageRunOut, status_code=202)
async def run_transform(
    run_id: Id,
    body: TransformStageRequest,
    session: AsyncSession = Depends(get_session),
    queue: JobQueue = Depends(get_queue),
    events: EventBus = Depends(get_events),
) -> StageRunOut:
    return await _start_query(session, queue, events, run_id, "transform", body)


@router.post("/query-runs/{run_id}/stages/retrieve", response_model=StageRunOut, status_code=202)
async def run_retrieve(
    run_id: Id,
    body: RetrieveStageRequest,
    session: AsyncSession = Depends(get_session),
    queue: JobQueue = Depends(get_queue),
    events: EventBus = Depends(get_events),
) -> StageRunOut:
    return await _start_query(session, queue, events, run_id, "retrieve", body)


@router.post("/query-runs/{run_id}/stages/rerank", response_model=StageRunOut, status_code=202)
async def run_rerank(
    run_id: Id,
    body: RerankStageRequest,
    session: AsyncSession = Depends(get_session),
    queue: JobQueue = Depends(get_queue),
    events: EventBus = Depends(get_events),
) -> StageRunOut:
    return await _start_query(session, queue, events, run_id, "rerank", body)


@router.post("/query-runs/{run_id}/stages/generate", response_model=StageRunOut, status_code=202)
async def run_generate(
    run_id: Id,
    body: GenerateStageRequest,
    session: AsyncSession = Depends(get_session),
    queue: JobQueue = Depends(get_queue),
    events: EventBus = Depends(get_events),
) -> StageRunOut:
    return await _start_query(session, queue, events, run_id, "generate", body)


@router.post("/query-runs/{run_id}/run-all", response_model=QueryRunOut)
async def run_all_query(
    run_id: Id,
    body: QueryRunAllRequest,
    session: AsyncSession = Depends(get_session),
    queue: JobQueue = Depends(get_queue),
    events: EventBus = Depends(get_events),
) -> JSONResponse:
    run = await query_runs.load_query_run(session, run_id)
    params = body.params.model_dump(mode="json")
    queued = await run_all.start_run_all(session, queue, events, run, body.from_stage, params)
    out = await query_runs.query_run_out(session, run_id)
    return JSONResponse(status_code=202 if queued else 200, content=out.model_dump(mode="json"))
