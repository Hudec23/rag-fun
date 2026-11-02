"""Tests for rag_api.services.job_payloads: envelope, file_block, build_payload for the
ingest stages. Payloads are validated against contracts/jobs/{stage}.schema.json via
tests.contract.errors. The service is still a stub — every test here is red until
T-api-014."""

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.models import (
    BatchRow,
    CollectionRow,
    FileRow,
    IngestRunRow,
    StageRunRow,
)
from rag_api.services import job_payloads
from tests.conftest import FIXTURES, add_collection, add_settings
from tests.contract import errors

B_1 = "019a4b2c-1e00-7b00-8000-000000000001"
F_1 = "019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a01"
R_1 = "019a4b2c-2000-7c00-9000-000000000002"
SR_PARSE = "019a4b2c-2100-7c00-9000-0000000000c1"
SR_CHUNK = "019a4b2c-2100-7c00-9000-0000000000c2"
SR_EMBED = "019a4b2c-2100-7c00-9000-0000000000c3"
SR_STORE = "019a4b2c-2100-7c00-9000-0000000000c4"
SR_OF = {"parse": SR_PARSE, "chunk": SR_CHUNK, "embed": SR_EMBED, "store": SR_STORE}

T_OLD = datetime(2026, 11, 1, 18, 22, 3, 123000, tzinfo=UTC)

DATA = b"hello file"
SHA = "0" * 64
S3_KEY = f"{B_1}/{F_1}/q3-report.pdf"
OLLAMA_URL = "http://ollama-fake:11434"

FILE_BLOCK = {
    "file_id": F_1,
    "batch_id": B_1,
    "batch_name": "Q3 reports",
    "filename": "q3-report.pdf",
    "mime": "application/pdf",
    "s3_key": S3_KEY,
    "tags": ["a", "b"],
}
DENSE = {"model": "bge-m3", "dims": 1024, "ollama_url": OLLAMA_URL}


def stage_params(stage: str) -> dict[str, Any]:
    """params for a stage row, copied from the contract fixture jobs__<stage>.json."""
    return json.loads((FIXTURES / f"jobs__{stage}.json").read_text())["params"]


def collection_block(col: CollectionRow) -> dict[str, Any]:
    return {
        "id": col.id,
        "qdrant_name": col.qdrant_name,
        "dense": DENSE,
        "sparse_model": "Qdrant/bm25",
    }


async def add_batch(session: AsyncSession) -> BatchRow:
    row = BatchRow(id=B_1, name="Q3 reports", tags=["a", "b"], created_at=T_OLD)
    session.add(row)
    await session.flush()
    return row


async def add_file(session: AsyncSession) -> FileRow:
    row = FileRow(
        id=F_1,
        batch_id=B_1,
        filename="q3-report.pdf",
        mime="application/pdf",
        size_bytes=len(DATA),
        sha256=SHA,
        s3_key=S3_KEY,
        tags=["b"],
        created_at=T_OLD,
    )
    session.add(row)
    await session.flush()
    return row


async def add_ingest_run(session: AsyncSession, collection_id: str) -> IngestRunRow:
    row = IngestRunRow(
        id=R_1,
        file_id=F_1,
        collection_id=collection_id,
        run_all_plan=[],
        created_at=T_OLD,
    )
    session.add(row)
    await session.flush()
    return row


async def add_stage_run(
    session: AsyncSession,
    stage: str,
    status: str,
    *,
    artifact_key: str | None = None,
) -> StageRunRow:
    row = StageRunRow(
        id=SR_OF[stage],
        run_id=R_1,
        run_kind="ingest",
        stage=stage,
        version=1,
        params=stage_params(stage),
        status=status,
        artifact_key=artifact_key,
        created_at=T_OLD,
    )
    session.add(row)
    await session.flush()
    return row


def test_envelope_copies_stage_run_fields() -> None:
    row = StageRunRow(
        id=SR_PARSE,
        run_id=R_1,
        run_kind="ingest",
        stage="parse",
        version=1,
        params=stage_params("parse"),
        status="queued",
        created_at=T_OLD,
    )

    assert job_payloads.envelope(row) == {
        "stage_run_id": SR_PARSE,
        "run_id": R_1,
        "run_kind": "ingest",
        "stage": "parse",
        "version": 1,
    }


async def test_file_block_copies_file_fields_and_sorted_tag_union(
    session: AsyncSession, frozen_now: object
) -> None:
    col = await add_collection(session, "docs")
    await add_batch(session)
    await add_file(session)
    run = await add_ingest_run(session, col.id)

    assert await job_payloads.file_block(session, run) == FILE_BLOCK


async def test_parse_payload_validates_against_jobs_parse_schema(
    session: AsyncSession, frozen_now: object
) -> None:
    col = await add_collection(session, "docs")
    await add_batch(session)
    await add_file(session)
    run = await add_ingest_run(session, col.id)
    row = await add_stage_run(session, "parse", "queued")

    payload = await job_payloads.build_payload(session, run, row, {})

    assert payload["stage_run_id"] == SR_PARSE
    assert payload["run_id"] == R_1
    assert payload["run_kind"] == "ingest"
    assert payload["stage"] == "parse"
    assert payload["version"] == 1
    assert payload["params"] == stage_params("parse")
    assert payload["file"] == FILE_BLOCK
    assert errors(payload, "jobs/parse.schema.json") == []


async def test_chunk_payload_takes_active_parse_key_and_dense_from_collection(
    session: AsyncSession, frozen_now: object
) -> None:
    col = await add_collection(session, "docs")
    await add_settings(session)
    await add_batch(session)
    await add_file(session)
    run = await add_ingest_run(session, col.id)
    parse = await add_stage_run(session, "parse", "done", artifact_key=f"{R_1}/parse/v1.json")
    row = await add_stage_run(session, "chunk", "queued")

    payload = await job_payloads.build_payload(session, run, row, {"parse": parse})

    assert payload["parse_artifact_key"] == f"{R_1}/parse/v1.json"
    assert payload["dense"] == DENSE
    assert payload["file"] == FILE_BLOCK
    assert payload["params"] == stage_params("chunk")
    assert errors(payload, "jobs/chunk.schema.json") == []


async def test_embed_and_store_payloads_validate_with_strategies_from_active_rows(
    session: AsyncSession, frozen_now: object
) -> None:
    col = await add_collection(session, "docs")
    await add_settings(session)
    await add_batch(session)
    await add_file(session)
    run = await add_ingest_run(session, col.id)
    parse = await add_stage_run(session, "parse", "done", artifact_key=f"{R_1}/parse/v1.json")
    chunk = await add_stage_run(session, "chunk", "done", artifact_key=f"{R_1}/chunk/v1.json")
    embed = await add_stage_run(session, "embed", "done", artifact_key=f"{R_1}/embed/v1.json")
    row = await add_stage_run(session, "store", "queued")

    embed_payload = await job_payloads.build_payload(
        session, run, embed, {"parse": parse, "chunk": chunk}
    )

    assert embed_payload["chunk_artifact_key"] == f"{R_1}/chunk/v1.json"
    assert embed_payload["collection"] == collection_block(col)
    assert embed_payload["params"] == stage_params("embed")
    assert errors(embed_payload, "jobs/embed.schema.json") == []

    store_payload = await job_payloads.build_payload(
        session, run, row, {"parse": parse, "chunk": chunk, "embed": embed}
    )

    assert store_payload["file"] == FILE_BLOCK
    assert store_payload["chunk_artifact_key"] == f"{R_1}/chunk/v1.json"
    assert store_payload["embed_artifact_key"] == f"{R_1}/embed/v1.json"
    assert store_payload["collection"] == collection_block(col)
    assert store_payload["parse_strategy"] == "docling_layout"
    assert store_payload["chunk_strategy"] == "recursive"
    assert store_payload["params"] == stage_params("store")
    assert errors(store_payload, "jobs/store.schema.json") == []
