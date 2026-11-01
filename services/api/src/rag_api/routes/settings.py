import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.session import get_session
from rag_api.deps import get_http
from rag_api.schemas.settings import (
    SettingsOut,
    SettingsUpdate,
    TestConnectionRequest,
    TestConnectionResult,
)
from rag_api.services import app_settings, connection_test

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
async def get_settings(session: AsyncSession = Depends(get_session)) -> SettingsOut:
    return await app_settings.get_settings_out(session)


@router.put("", response_model=SettingsOut)
async def put_settings(
    body: SettingsUpdate, session: AsyncSession = Depends(get_session)
) -> SettingsOut:
    return await app_settings.put_settings(session, body)


@router.post("/test-connection", response_model=TestConnectionResult)
async def test_connection(
    body: TestConnectionRequest,
    session: AsyncSession = Depends(get_session),
    http: httpx.AsyncClient = Depends(get_http),
) -> TestConnectionResult:
    return await connection_test.test_connection(session, http, body)
