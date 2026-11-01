from typing import Any, Literal

from rag_api.contracts_gen.shared.common_schema import ErrorBody
from rag_api.contracts_gen.shared.summary_schema import StageSummary
from rag_api.schemas.base import Id, Model, Timestamp

ComponentName = Literal[
    "api", "worker-ingest", "worker-query", "postgres", "redis", "qdrant", "s3", "ollama"
]
COMPONENT_ORDER: list[ComponentName] = [
    "api",
    "worker-ingest",
    "worker-query",
    "postgres",
    "redis",
    "qdrant",
    "s3",
    "ollama",
]


class Health(Model):
    status: Literal["ok"] = "ok"
    service: Literal["api"] = "api"
    version: str


class ComponentStatus(Model):
    name: ComponentName
    ok: bool
    latency_ms: int
    detail: str | None


class Status(Model):
    components: list[ComponentStatus]


class PipelineGraphList(Model):
    items: list[dict[str, Any]]  # contracts/shared/pipeline-graph.schema.json


class StageStarted(Model):
    stage_run_id: Id
    started_at: Timestamp


class StageResult(Model):
    stage_run_id: Id
    status: Literal["done", "failed"]
    artifact_key: str | None
    summary: StageSummary | None
    error: ErrorBody | None
    started_at: Timestamp
    finished_at: Timestamp
