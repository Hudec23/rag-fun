from typing import Any, Literal

from pydantic import Field

from rag_api.contracts_gen.shared.common_schema import (
    ChunkParams,
    EmbedParams,
    GenerateParams,
    ParseParams,
    RerankParams,
    RetrieveParams,
    StoreParams,
    TransformParams,
)
from rag_api.schemas.base import Id, Model, PageInfo, Timestamp
from rag_api.schemas.files import FileOut

IngestStage = Literal["parse", "chunk", "embed", "store"]
QueryStage = Literal["transform", "retrieve", "rerank", "generate"]
Stage = Literal["parse", "chunk", "embed", "store", "transform", "retrieve", "rerank", "generate"]
StageStatus = Literal["queued", "running", "done", "failed", "stale"]


class StageRunOut(Model):
    id: Id
    run_id: Id
    run_kind: Literal["ingest", "query"]
    stage: Stage
    version: int
    params: dict[str, Any]  # shape = the stage's params schema
    status: StageStatus
    artifact_key: str | None
    summary: dict[str, Any] | None
    error: dict[str, Any] | None
    created_at: Timestamp
    started_at: Timestamp | None
    finished_at: Timestamp | None


class StageRunList(Model):
    items: list[StageRunOut]


class IngestStages(Model):
    parse: StageRunOut | None
    chunk: StageRunOut | None
    embed: StageRunOut | None
    store: StageRunOut | None


class QueryStages(Model):
    transform: StageRunOut | None
    retrieve: StageRunOut | None
    rerank: StageRunOut | None
    generate: StageRunOut | None


class IngestRunCreate(Model):
    file_id: Id
    collection_id: Id


class IngestRunOut(Model):
    id: Id
    file: FileOut
    collection_id: Id
    created_at: Timestamp
    run_all_pending: list[IngestStage]
    stages: IngestStages


class IngestRunPage(Model):
    items: list[IngestRunOut]
    page: PageInfo


class IngestRunList(Model):
    items: list[IngestRunOut]


class QueryRunCreate(Model):
    collection_id: Id
    question: str = Field(min_length=1, max_length=2000)


class QueryRunOut(Model):
    id: Id
    collection_id: Id
    question: str
    created_at: Timestamp
    run_all_pending: list[QueryStage]
    stages: QueryStages


class QueryRunPage(Model):
    items: list[QueryRunOut]
    page: PageInfo


class ParseStageRequest(Model):
    params: ParseParams


class ChunkStageRequest(Model):
    params: ChunkParams


class EmbedStageRequest(Model):
    params: EmbedParams


class StoreStageRequest(Model):
    params: StoreParams


class TransformStageRequest(Model):
    params: TransformParams


class RetrieveStageRequest(Model):
    params: RetrieveParams


class RerankStageRequest(Model):
    params: RerankParams


class GenerateStageRequest(Model):
    params: GenerateParams


class IngestParamsAll(Model):
    parse: ParseParams
    chunk: ChunkParams
    embed: EmbedParams
    store: StoreParams


class QueryParamsAll(Model):
    transform: TransformParams
    retrieve: RetrieveParams
    rerank: RerankParams
    generate: GenerateParams


class IngestRunAllRequest(Model):
    from_stage: IngestStage | None
    params: IngestParamsAll


class QueryRunAllRequest(Model):
    from_stage: QueryStage | None
    params: QueryParamsAll


class BatchIngestRequest(Model):
    collection_id: Id
    params: IngestParamsAll
