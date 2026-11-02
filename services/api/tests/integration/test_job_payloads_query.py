"""Tests for rag_api.services.job_payloads.build_payload for the query stages (transform,
retrieve, rerank, generate). Payloads are validated against contracts/jobs/{stage}.schema.json
via tests.contract.errors."""

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.models import QueryRunRow, StageRunRow
from rag_api.services import app_settings, job_payloads
from tests.conftest import FIXTURES, add_collection, add_settings
from tests.contract import errors

Q_1 = "019a4b2c-2000-7c00-9000-0000000000a1"
SR_TRANSFORM = "019a4b2c-2100-7c00-9000-0000000000d1"
SR_RETRIEVE = "019a4b2c-2100-7c00-9000-0000000000d2"
SR_RERANK = "019a4b2c-2100-7c00-9000-0000000000d3"
SR_GENERATE = "019a4b2c-2100-7c00-9000-0000000000d4"
SR_OF = {
    "transform": SR_TRANSFORM,
    "retrieve": SR_RETRIEVE,
    "rerank": SR_RERANK,
    "generate": SR_GENERATE,
}
QUESTION = "What was Q3 revenue?"

T_OLD = datetime(2026, 11, 1, 18, 22, 3, 123000, tzinfo=UTC)


def stage_params(stage: str) -> dict[str, Any]:
    """params for a stage row, copied from the contract fixture jobs__<stage>.json."""
    return json.loads((FIXTURES / f"jobs__{stage}.json").read_text())["params"]


async def add_query_run(session: AsyncSession, collection_id: str) -> QueryRunRow:
    row = QueryRunRow(
        id=Q_1,
        collection_id=collection_id,
        question=QUESTION,
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
        run_id=Q_1,
        run_kind="query",
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


async def test_transform_payload_validates_and_carries_resolved_chat(
    session: AsyncSession, frozen_now: object
) -> None:
    col = await add_collection(session, "docs")
    await add_settings(session)
    run = await add_query_run(session, col.id)
    row = await add_stage_run(session, "transform", "queued")

    payload = await job_payloads.build_payload(session, run, row, {})

    assert payload["stage_run_id"] == SR_TRANSFORM
    assert payload["run_id"] == Q_1
    assert payload["run_kind"] == "query"
    assert payload["stage"] == "transform"
    assert payload["question"] == QUESTION
    assert payload["params"] == stage_params("transform")
    assert payload["chat"] == await app_settings.resolve_chat(session)
    assert errors(payload, "jobs/transform.schema.json") == []


async def test_generate_payload_uses_rerank_context_when_rerank_active(
    session: AsyncSession, frozen_now: object
) -> None:
    col = await add_collection(session, "docs")
    await add_settings(session)
    run = await add_query_run(session, col.id)
    retrieve = await add_stage_run(
        session, "retrieve", "done", artifact_key=f"{Q_1}/retrieve/v1.json"
    )
    rerank = await add_stage_run(session, "rerank", "done", artifact_key=f"{Q_1}/rerank/v1.json")
    row = await add_stage_run(session, "generate", "queued")

    payload = await job_payloads.build_payload(
        session, run, row, {"retrieve": retrieve, "rerank": rerank}
    )

    assert payload["context_source"] == "rerank"
    assert payload["context_artifact_key"] == f"{Q_1}/rerank/v1.json"
    assert payload["chat"] == await app_settings.resolve_chat(session)
    assert payload["question"] == QUESTION
    assert errors(payload, "jobs/generate.schema.json") == []


async def test_generate_payload_uses_retrieve_context_when_rerank_never_ran(
    session: AsyncSession, frozen_now: object
) -> None:
    col = await add_collection(session, "docs")
    await add_settings(session)
    run = await add_query_run(session, col.id)
    retrieve = await add_stage_run(
        session, "retrieve", "done", artifact_key=f"{Q_1}/retrieve/v1.json"
    )
    row = await add_stage_run(session, "generate", "queued")

    payload = await job_payloads.build_payload(session, run, row, {"retrieve": retrieve})

    assert payload["context_source"] == "retrieve"
    assert payload["context_artifact_key"] == f"{Q_1}/retrieve/v1.json"
    assert payload["chat"] == await app_settings.resolve_chat(session)
    assert errors(payload, "jobs/generate.schema.json") == []


async def test_retrieve_payload_has_no_transform_key_when_transform_never_ran(
    session: AsyncSession, frozen_now: object
) -> None:
    col = await add_collection(session, "docs")
    await add_settings(session)
    run = await add_query_run(session, col.id)
    row = await add_stage_run(session, "retrieve", "queued")

    payload = await job_payloads.build_payload(session, run, row, {})

    assert payload["transform_artifact_key"] is None
    assert payload["collection"]["id"] == col.id
    assert payload["collection"]["qdrant_name"] == col.qdrant_name
    assert payload["params"] == stage_params("retrieve")
    assert errors(payload, "jobs/retrieve.schema.json") == []


async def test_rerank_payload_uses_settings_reranker_model(
    session: AsyncSession, frozen_now: object
) -> None:
    col = await add_collection(session, "docs")
    await add_settings(session)
    run = await add_query_run(session, col.id)
    retrieve = await add_stage_run(
        session, "retrieve", "done", artifact_key=f"{Q_1}/retrieve/v1.json"
    )
    row = await add_stage_run(session, "rerank", "queued")

    payload = await job_payloads.build_payload(session, run, row, {"retrieve": retrieve})

    assert payload["model"] == await app_settings.reranker_model(session)
    assert payload["retrieve_artifact_key"] == f"{Q_1}/retrieve/v1.json"
    assert payload["params"] == stage_params("rerank")
    assert errors(payload, "jobs/rerank.schema.json") == []
