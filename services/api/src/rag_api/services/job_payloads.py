"""Build worker job payloads (contracts/jobs/{stage}.schema.json) for a freshly queued stage run."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.models import IngestRunRow, QueryRunRow, StageRunRow


def envelope(row: StageRunRow) -> dict[str, Any]:
    """{'stage_run_id', 'run_id', 'run_kind', 'stage', 'version'} from the row."""
    raise NotImplementedError("not implemented")


async def file_block(session: AsyncSession, run: IngestRunRow) -> dict[str, Any]:
    """jobs 'file' object: file_id, batch_id, batch_name, filename, mime, s3_key,
    tags = sorted(set(file.tags) | set(batch.tags))."""
    raise NotImplementedError("not implemented")


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
    raise NotImplementedError("not implemented")
