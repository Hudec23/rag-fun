"""Integration tests for rag_api.services.app_settings: get/put/resolve.
Real postgres via the `session` fixture; the settings row is seeded directly with the
`add_settings` factory so the tests do not depend on the API routes.
The service is still a stub — every test here is red until T-api-012."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.models import SettingsRow
from rag_api.errors import AppError
from rag_api.schemas.settings import (
    AnthropicSettingsIn,
    OllamaSettings,
    OpenAICompatSettingsIn,
    SettingsUpdate,
)
from rag_api.services import app_settings
from tests.conftest import add_settings

ANTHROPIC_KEY = "sk-ant-secret-abcd"
ANTHROPIC_MODEL = "claude-sonnet-5-5"
OLLAMA_MODEL = "qwen3:8b"
OLLAMA_URL = "http://ollama-fake:11434"
OPENAI_BASE_URL = "http://openai-fake:8080/v1"
OPENAI_KEY = "sk-openai-fake-key"
OPENAI_MODEL = "gpt-fake"

APP_VALUE = {
    "chat_provider": "ollama",
    "ollama": {"url": OLLAMA_URL, "chat_model": OLLAMA_MODEL},
    "anthropic": {"model": ANTHROPIC_MODEL, "api_key": None},
    "openai_compatible": {"base_url": None, "model": None, "api_key": None},
    "reranker_model": "Xenova/ms-marco-MiniLM-L-6-v2",
}


def make_update(
    chat_provider: str,
    anthropic_api_key: str | None,
    base_url: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
) -> SettingsUpdate:
    return SettingsUpdate(
        chat_provider=chat_provider,
        ollama=OllamaSettings(url=OLLAMA_URL, chat_model=OLLAMA_MODEL),
        anthropic=AnthropicSettingsIn(model=ANTHROPIC_MODEL, api_key=anthropic_api_key),
        openai_compatible=OpenAICompatSettingsIn(base_url=base_url, model=model, api_key=api_key),
        reranker_model="Xenova/ms-marco-MiniLM-L-6-v2",
    )


def test_mask_key_none_empty_short_and_long() -> None:
    assert app_settings.mask_key(None) is None
    assert app_settings.mask_key("") is None
    assert app_settings.mask_key("abc") == "…bc"
    assert app_settings.mask_key("sk-ant-secret-abcd") == "sk-…abcd"


async def test_get_settings_out_default_row(session: AsyncSession, frozen_now: object) -> None:
    await add_settings(session)

    out = await app_settings.get_settings_out(session)

    assert out.model_dump() == {
        "chat_provider": "ollama",
        "ollama": {"url": OLLAMA_URL, "chat_model": OLLAMA_MODEL},
        "anthropic": {"model": ANTHROPIC_MODEL, "api_key_set": False, "api_key_masked": None},
        "openai_compatible": {
            "base_url": None,
            "model": None,
            "api_key_set": False,
            "api_key_masked": None,
        },
        "reranker_model": "Xenova/ms-marco-MiniLM-L-6-v2",
        "updated_at": "2026-11-01T18:22:05.123Z",
    }


async def test_put_settings_anthropic_api_key_stored_in_clear_and_masked_in_out(
    session: AsyncSession, frozen_now: object
) -> None:
    await add_settings(session)

    out = await app_settings.put_settings(session, make_update("anthropic", ANTHROPIC_KEY))

    assert out.anthropic.api_key_set is True
    assert out.anthropic.api_key_masked == "sk-…abcd"
    assert out.updated_at == "2026-11-01T18:22:05.123Z"
    row = (await session.execute(select(SettingsRow))).scalars().one()
    assert row.value["anthropic"]["api_key"] == ANTHROPIC_KEY


async def test_put_settings_api_key_none_keeps_stored_key_and_empty_removes_it(
    session: AsyncSession, frozen_now: object
) -> None:
    await add_settings(
        session,
        value={**APP_VALUE, "anthropic": {"model": ANTHROPIC_MODEL, "api_key": ANTHROPIC_KEY}},
    )

    out = await app_settings.put_settings(session, make_update("ollama", None))

    assert out.anthropic.api_key_set is True
    assert out.anthropic.api_key_masked == "sk-…abcd"
    assert out.updated_at == "2026-11-01T18:22:05.123Z"
    row = (await session.execute(select(SettingsRow))).scalars().one()
    assert row.value["anthropic"]["api_key"] == ANTHROPIC_KEY

    out = await app_settings.put_settings(session, make_update("ollama", ""))

    assert out.anthropic.api_key_set is False
    assert out.anthropic.api_key_masked is None
    row = (await session.execute(select(SettingsRow))).scalars().one()
    assert row.value["anthropic"]["api_key"] is None


async def test_put_settings_anthropic_without_key_raises_validation_error(
    session: AsyncSession,
) -> None:
    await add_settings(session, value={**APP_VALUE, "chat_provider": "anthropic"})

    with pytest.raises(AppError) as exc:
        await app_settings.put_settings(session, make_update("anthropic", None))

    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.details == {"field": "anthropic.api_key"}


async def test_put_settings_openai_compatible_missing_base_url_or_model_raises_validation_error(
    session: AsyncSession,
) -> None:
    await add_settings(session)

    with pytest.raises(AppError) as exc:
        await app_settings.put_settings(
            session, make_update("openai_compatible", None, model=OPENAI_MODEL)
        )

    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.details == {"field": "openai_compatible.base_url"}

    with pytest.raises(AppError) as exc:
        await app_settings.put_settings(
            session, make_update("openai_compatible", None, base_url=OPENAI_BASE_URL)
        )

    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.details == {"field": "openai_compatible.model"}


async def test_resolve_chat_builds_chat_model_config_per_provider(
    session: AsyncSession, frozen_now: object
) -> None:
    row = await add_settings(session)

    assert await app_settings.resolve_chat(session) == {
        "provider": "ollama",
        "model": OLLAMA_MODEL,
        "base_url": OLLAMA_URL,
        "api_key": None,
    }

    row.value = {
        **APP_VALUE,
        "chat_provider": "anthropic",
        "anthropic": {"model": ANTHROPIC_MODEL, "api_key": ANTHROPIC_KEY},
    }
    await session.flush()

    assert await app_settings.resolve_chat(session) == {
        "provider": "anthropic",
        "model": ANTHROPIC_MODEL,
        "base_url": None,
        "api_key": ANTHROPIC_KEY,
    }

    row.value = {
        **APP_VALUE,
        "chat_provider": "openai_compatible",
        "openai_compatible": {
            "base_url": OPENAI_BASE_URL,
            "model": OPENAI_MODEL,
            "api_key": OPENAI_KEY,
        },
    }
    await session.flush()

    assert await app_settings.resolve_chat(session) == {
        "provider": "openai_compatible",
        "model": OPENAI_MODEL,
        "base_url": OPENAI_BASE_URL,
        "api_key": OPENAI_KEY,
    }


async def test_load_value_without_row_raises_internal_error(session: AsyncSession) -> None:
    with pytest.raises(AppError) as exc:
        await app_settings.load_value(session)

    assert exc.value.code == "INTERNAL_ERROR"
    assert exc.value.message == "settings not initialised"
