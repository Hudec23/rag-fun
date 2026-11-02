"""Settings row 'app' (R-020). Value shape: plan/services/api.schema.sql (settings table comment)."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.models import SettingsRow
from rag_api.errors import AppError
from rag_api.ids import to_iso, utcnow
from rag_api.schemas.settings import (
    AnthropicSettingsOut,
    OllamaSettings,
    OpenAICompatSettingsOut,
    SettingsOut,
    SettingsUpdate,
)


def mask_key(key: str | None) -> str | None:
    """None/'' -> None; len < 8 -> '…' + last 2 chars; else first 3 + '…' + last 4 ('sk-…abcd')."""
    if not key:
        return None
    if len(key) < 8:
        return "…" + key[-2:]
    return key[:3] + "…" + key[-4:]


async def load_row(session: AsyncSession) -> SettingsRow:
    row = await session.get(SettingsRow, "app")
    if row is None:
        raise AppError("INTERNAL_ERROR", message="settings not initialised")
    return row


async def load_value(session: AsyncSession) -> dict[str, Any]:
    """settings.value of key 'app'. Missing row -> AppError('INTERNAL_ERROR', 'settings not initialised')."""
    return (await load_row(session)).value


def to_out(row: SettingsRow) -> SettingsOut:
    value = row.value
    anthropic = value["anthropic"]
    openai = value["openai_compatible"]
    return SettingsOut(
        chat_provider=value["chat_provider"],
        ollama=OllamaSettings(url=value["ollama"]["url"], chat_model=value["ollama"]["chat_model"]),
        anthropic=AnthropicSettingsOut(
            model=anthropic["model"],
            api_key_set=anthropic["api_key"] is not None,
            api_key_masked=mask_key(anthropic["api_key"]),
        ),
        openai_compatible=OpenAICompatSettingsOut(
            base_url=openai["base_url"],
            model=openai["model"],
            api_key_set=openai["api_key"] is not None,
            api_key_masked=mask_key(openai["api_key"]),
        ),
        reranker_model=value["reranker_model"],
        updated_at=to_iso(row.updated_at),
    )


async def get_settings_out(session: AsyncSession) -> SettingsOut:
    return to_out(await load_row(session))


async def put_settings(session: AsyncSession, body: SettingsUpdate) -> SettingsOut:
    """api_key None keeps the stored key, '' deletes it, other replaces it.
    chat_provider anthropic without resulting key -> VALIDATION_ERROR (details.field='anthropic.api_key');
    openai_compatible without base_url or model -> VALIDATION_ERROR (field 'openai_compatible.base_url'
    or 'openai_compatible.model'). updated_at = utcnow."""
    row = await load_row(session)
    stored = row.value
    anthropic_key = stored["anthropic"]["api_key"]
    if body.anthropic.api_key is not None:
        anthropic_key = body.anthropic.api_key or None
    openai_key = stored["openai_compatible"]["api_key"]
    if body.openai_compatible.api_key is not None:
        openai_key = body.openai_compatible.api_key or None
    if body.chat_provider == "anthropic" and anthropic_key is None:
        raise AppError("VALIDATION_ERROR", details={"field": "anthropic.api_key"})
    if body.chat_provider == "openai_compatible":
        if not body.openai_compatible.base_url:
            raise AppError("VALIDATION_ERROR", details={"field": "openai_compatible.base_url"})
        if not body.openai_compatible.model:
            raise AppError("VALIDATION_ERROR", details={"field": "openai_compatible.model"})
    row.value = {
        "chat_provider": body.chat_provider,
        "ollama": {"url": body.ollama.url, "chat_model": body.ollama.chat_model},
        "anthropic": {"model": body.anthropic.model, "api_key": anthropic_key},
        "openai_compatible": {
            "base_url": body.openai_compatible.base_url,
            "model": body.openai_compatible.model,
            "api_key": openai_key,
        },
        "reranker_model": body.reranker_model,
    }
    row.updated_at = utcnow()
    await session.flush()
    return to_out(row)


async def resolve_chat(session: AsyncSession) -> dict[str, Any]:
    """ChatModelConfig for job payloads: ollama -> {provider, model: ollama.chat_model,
    base_url: ollama.url, api_key: None}; anthropic -> {model, base_url: None, api_key};
    openai_compatible -> {model, base_url, api_key}."""
    value = await load_value(session)
    provider = value["chat_provider"]
    if provider == "anthropic":
        anthropic = value["anthropic"]
        return {
            "provider": provider,
            "model": anthropic["model"],
            "base_url": None,
            "api_key": anthropic["api_key"],
        }
    if provider == "openai_compatible":
        openai = value["openai_compatible"]
        return {
            "provider": provider,
            "model": openai["model"],
            "base_url": openai["base_url"],
            "api_key": openai["api_key"],
        }
    ollama = value["ollama"]
    return {
        "provider": provider,
        "model": ollama["chat_model"],
        "base_url": ollama["url"],
        "api_key": None,
    }


async def ollama_url(session: AsyncSession) -> str:
    return (await load_value(session))["ollama"]["url"]


async def reranker_model(session: AsyncSession) -> str:
    return (await load_value(session))["reranker_model"]
