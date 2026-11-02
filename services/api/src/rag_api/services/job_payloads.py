"""Build worker job payloads (contracts/jobs/{stage}.schema.json) for a freshly queued stage run."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.models import BatchRow, FileRow, IngestRunRow, QueryRunRow, StageRunRow
from rag_api.errors import AppError
from rag_api.services import app_settings, collections

Run = IngestRunRow | QueryRunRow


def envelope(row: StageRunRow) -> dict[str, Any]:
    """{'stage_run_id', 'run_id', 'run_kind', 'stage', 'version'} from the row."""
    return {
        "stage_run_id": row.id,
        "run_id": row.run_id,
        "run_kind": row.run_kind,
        "stage": row.stage,
        "version": row.version,
    }


async def file_block(session: AsyncSession, run: IngestRunRow) -> dict[str, Any]:
    """jobs 'file' object: file_id, batch_id, batch_name, filename, mime, s3_key,
    tags = sorted(set(file.tags) | set(batch.tags))."""
    file = await session.get(FileRow, run.file_id)
    if file is None:
        raise AppError("FILE_NOT_FOUND", details={"file_id": run.file_id})
    batch = await session.get(BatchRow, file.batch_id)
    if batch is None:
        raise AppError("BATCH_NOT_FOUND", details={"batch_id": file.batch_id})
    return {
        "file_id": file.id,
        "batch_id": batch.id,
        "batch_name": batch.name,
        "filename": file.filename,
        "mime": file.mime,
        "s3_key": file.s3_key,
        "tags": sorted(set(file.tags) | set(batch.tags)),
    }


def _active(latest: dict[str, StageRunRow], stage: str) -> StageRunRow | None:
    """latest[stage] if its status is 'done', else None (stages.active_row)."""
    row = latest.get(stage)
    if row is not None and row.status == "done":
        return row
    return None


def _upstream_key(stage: str, latest: dict[str, StageRunRow], upstream: str) -> str:
    """artifact_key of the active `upstream` row; else AppError('STAGE_PREREQUISITE_MISSING')."""
    row = _active(latest, upstream)
    if row is None or row.artifact_key is None:
        raise AppError("STAGE_PREREQUISITE_MISSING", details={"stage": stage, "missing": upstream})
    return row.artifact_key


def _upstream_params(stage: str, latest: dict[str, StageRunRow], upstream: str) -> dict[str, Any]:
    """params of the active `upstream` row; else AppError('STAGE_PREREQUISITE_MISSING')."""
    row = _active(latest, upstream)
    if row is None:
        raise AppError("STAGE_PREREQUISITE_MISSING", details={"stage": stage, "missing": upstream})
    return row.params


async def _dense(session: AsyncSession, run: Run) -> dict[str, Any]:
    """Dense model config of the run's collection, ollama_url from the app settings."""
    col = await collections.load_collection(session, run.collection_id)
    return {
        "model": col.dense_model,
        "dims": col.dense_dims,
        "ollama_url": await app_settings.ollama_url(session),
    }


async def _collection_ref(session: AsyncSession, run: Run) -> dict[str, object]:
    """CollectionRef of the run's collection (collections.collection_ref), ollama_url from settings."""
    col = await collections.load_collection(session, run.collection_id)
    return collections.collection_ref(col, await app_settings.ollama_url(session))


async def build_payload(
    session: AsyncSession,
    run: IngestRunRow | QueryRunRow,
    row: StageRunRow,
    latest: dict[str, StageRunRow],
) -> dict[str, Any]:
    """envelope + params + stage specific fields. `latest` = rows BEFORE `row` was inserted.
    parse: file. chunk: file, parse_artifact_key (active parse), dense (collection dense model config,
    ollama_url from settings). embed: chunk_artifact_key, collection (CollectionRef).
    store: file, chunk_artifact_key, embed_artifact_key, collection, parse_strategy, chunk_strategy
    (from the active parse/chunk rows' params). transform: question, chat (app_settings.resolve_chat).
    retrieve: question, transform_artifact_key (active transform or None), collection.
    rerank: question, retrieve_artifact_key, model (app_settings reranker_model).
    generate: question, context_artifact_key + context_source ('rerank' if rerank active else
    'retrieve'), chat. The result must validate against contracts/jobs/{stage}.schema.json."""
    stage = row.stage
    payload: dict[str, Any] = {**envelope(row), "params": row.params}
    if isinstance(run, IngestRunRow):
        if stage not in ("parse", "chunk", "embed", "store"):
            raise AppError("INTERNAL_ERROR", details={"stage": stage})
        if stage in ("parse", "chunk", "store"):
            payload["file"] = await file_block(session, run)
        if stage == "chunk":
            payload["parse_artifact_key"] = _upstream_key(stage, latest, "parse")
            payload["dense"] = await _dense(session, run)
        if stage == "embed":
            payload["chunk_artifact_key"] = _upstream_key(stage, latest, "chunk")
            payload["collection"] = await _collection_ref(session, run)
        if stage == "store":
            payload["chunk_artifact_key"] = _upstream_key(stage, latest, "chunk")
            payload["embed_artifact_key"] = _upstream_key(stage, latest, "embed")
            payload["collection"] = await _collection_ref(session, run)
            payload["parse_strategy"] = _upstream_params(stage, latest, "parse")["strategy"]
            payload["chunk_strategy"] = _upstream_params(stage, latest, "chunk")["strategy"]
    else:
        if stage not in ("transform", "retrieve", "rerank", "generate"):
            raise AppError("INTERNAL_ERROR", details={"stage": stage})
        payload["question"] = run.question
        if stage == "transform":
            payload["chat"] = await app_settings.resolve_chat(session)
        if stage == "retrieve":
            transform = _active(latest, "transform")
            payload["transform_artifact_key"] = transform.artifact_key if transform else None
            payload["collection"] = await _collection_ref(session, run)
        if stage == "rerank":
            payload["retrieve_artifact_key"] = _upstream_key(stage, latest, "retrieve")
            payload["model"] = await app_settings.reranker_model(session)
        if stage == "generate":
            rerank = _active(latest, "rerank")
            if rerank is not None:
                payload["context_artifact_key"] = rerank.artifact_key
                payload["context_source"] = "rerank"
            else:
                payload["context_artifact_key"] = _upstream_key(stage, latest, "retrieve")
                payload["context_source"] = "retrieve"
            payload["chat"] = await app_settings.resolve_chat(session)
    return payload
