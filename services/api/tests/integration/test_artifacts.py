"""Integration tests for rag_api.services.artifacts: get_stage_run, list_stage_runs,
get_artifact, get_page_image. The `session` fixture (postgres-test) plus the `store`
(FakeObjectStore) and `settings` fixtures drive the service functions directly.
The service is still a stub — every test here is red until T-api-019."""

import json
from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.config import Settings
from rag_api.db.models import StageRunRow
from rag_api.errors import AppError
from rag_api.services import artifacts
from tests.conftest import FIXTURES
from tests.fakes import FakeObjectStore

R_1 = "019a4b2c-1a00-7b00-8000-0000000000a1"
R_MISSING = "019a4b2c-1a00-7b00-8000-0000000000a9"
SR_1 = "019a4b2c-1c00-7b00-8000-0000000000c1"
SR_2 = "019a4b2c-1c00-7b00-8000-0000000000c2"
SR_3 = "019a4b2c-1c00-7b00-8000-0000000000c3"
SR_MISSING = "019a4b2c-1c00-7b00-8000-0000000000c9"

T_OLD = datetime(2026, 11, 1, 18, 22, 3, 123000, tzinfo=UTC)

KEY_1 = "019a4b2c-2000-7c00-9000-000000000002/parse/v1.json"
KEY_2 = "019a4b2c-2000-7c00-9000-000000000002/parse/v2.json"
KEY_3 = "019a4b2c-2000-7c00-9000-000000000002/parse/v3.json"
PAGE_1_KEY = "019a4b2c-2000-7c00-9000-000000000002/parse/v1/page-1.png"
PNG = b"\x89PNG"

PARSE_BYTES = (FIXTURES / "artifact_parse.json").read_bytes()


async def add_stage_run(
    session: AsyncSession,
    stage_run_id: str,
    run_id: str,
    stage: str,
    status: str,
    *,
    version: int = 1,
    artifact_key: str | None = None,
    summary: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
) -> StageRunRow:
    row = StageRunRow(
        id=stage_run_id,
        run_id=run_id,
        run_kind="ingest",
        stage=stage,
        version=version,
        params={},
        status=status,
        artifact_key=artifact_key,
        summary=summary,
        error=error,
        created_at=T_OLD,
        started_at=started_at,
        finished_at=finished_at,
    )
    session.add(row)
    await session.flush()
    return row


async def test_get_stage_run_unknown_raises_stage_run_not_found(session: AsyncSession) -> None:
    with pytest.raises(AppError) as exc:
        await artifacts.get_stage_run(session, SR_MISSING)
    assert exc.value.code == "STAGE_RUN_NOT_FOUND"
    assert exc.value.details == {"stage_run_id": SR_MISSING}


async def test_list_stage_runs_returns_versions_desc_and_empty_for_unknown_run(
    session: AsyncSession,
) -> None:
    await add_stage_run(session, SR_1, R_1, "parse", "queued", version=1)
    await add_stage_run(session, SR_2, R_1, "parse", "done", version=2)
    await add_stage_run(session, SR_3, R_1, "chunk", "done")

    result = await artifacts.list_stage_runs(session, R_1, "parse")

    assert [item.id for item in result.items] == [SR_2, SR_1]
    assert [item.version for item in result.items] == [2, 1]

    empty = await artifacts.list_stage_runs(session, R_MISSING, "parse")
    assert empty.items == []


async def test_get_artifact_returns_stored_bytes_unchanged(
    session: AsyncSession, store: FakeObjectStore, settings: Settings
) -> None:
    await add_stage_run(session, SR_1, R_1, "parse", "done", artifact_key=KEY_1)
    store.objects[("artifacts", KEY_1)] = (PARSE_BYTES, "application/json")

    data = await artifacts.get_artifact(session, store, settings, SR_1)

    assert data == PARSE_BYTES


async def test_get_artifact_missing_artifact_raises_artifact_not_found(
    session: AsyncSession, store: FakeObjectStore, settings: Settings
) -> None:
    # artifact_key is None.
    await add_stage_run(session, SR_1, R_1, "parse", "done")
    with pytest.raises(AppError) as exc:
        await artifacts.get_artifact(session, store, settings, SR_1)
    assert exc.value.code == "ARTIFACT_NOT_FOUND"
    assert exc.value.details == {"stage_run_id": SR_1}

    # artifact_key set but the object is missing from the store.
    await add_stage_run(session, SR_2, R_1, "chunk", "done", artifact_key=KEY_2)
    with pytest.raises(AppError) as exc:
        await artifacts.get_artifact(session, store, settings, SR_2)
    assert exc.value.code == "ARTIFACT_NOT_FOUND"
    assert exc.value.details == {"stage_run_id": SR_2}


async def test_get_page_image_returns_png_bytes_from_parse_artifact(
    session: AsyncSession, store: FakeObjectStore, settings: Settings
) -> None:
    await add_stage_run(session, SR_1, R_1, "parse", "done", artifact_key=KEY_1)
    store.objects[("artifacts", KEY_1)] = (PARSE_BYTES, "application/json")
    store.objects[("artifacts", PAGE_1_KEY)] = (PNG, "image/png")

    data = await artifacts.get_page_image(session, store, settings, SR_1, 1)

    assert data == PNG


async def test_get_page_image_missing_page_raises_page_not_found(
    session: AsyncSession, store: FakeObjectStore, settings: Settings
) -> None:
    # Page 9 is not in the parse artifact (it has pages 1 and 2).
    await add_stage_run(session, SR_1, R_1, "parse", "done", artifact_key=KEY_1)
    store.objects[("artifacts", KEY_1)] = (PARSE_BYTES, "application/json")
    with pytest.raises(AppError) as exc:
        await artifacts.get_page_image(session, store, settings, SR_1, 9)
    assert exc.value.code == "PAGE_NOT_FOUND"
    assert exc.value.details == {"page_no": 9}

    # Not a parse stage run.
    await add_stage_run(session, SR_2, R_1, "chunk", "done", artifact_key=KEY_2)
    with pytest.raises(AppError) as exc:
        await artifacts.get_page_image(session, store, settings, SR_2, 1)
    assert exc.value.code == "PAGE_NOT_FOUND"
    assert exc.value.details == {"page_no": 1}

    # Parse artifact whose page 1 has image_key None.
    artifact = json.loads(PARSE_BYTES)
    artifact["pages"][0]["image_key"] = None
    no_image = json.dumps(artifact).encode()
    await add_stage_run(session, SR_3, R_1, "parse", "done", artifact_key=KEY_3)
    store.objects[("artifacts", KEY_3)] = (no_image, "application/json")
    with pytest.raises(AppError) as exc:
        await artifacts.get_page_image(session, store, settings, SR_3, 1)
    assert exc.value.code == "PAGE_NOT_FOUND"
    assert exc.value.details == {"page_no": 1}
