"""Settings row 'app' (R-020). Value shape: plan/services/api.schema.sql (settings table comment)."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.schemas.settings import SettingsOut, SettingsUpdate


def mask_key(key: str | None) -> str | None:
    """None/'' -> None; len < 8 -> '…' + last 2 chars; else first 3 + '…' + last 4 ('sk-…abcd')."""
    raise NotImplementedError("not implemented")


async def load_value(session: AsyncSession) -> dict[str, Any]:
    """settings.value of key 'app'. Missing row -> AppError('INTERNAL_ERROR', 'settings not initialised')."""
    raise NotImplementedError("not implemented")


async def get_settings_out(session: AsyncSession) -> SettingsOut:
    raise NotImplementedError("not implemented")


async def put_settings(session: AsyncSession, body: SettingsUpdate) -> SettingsOut:
    """api_key None keeps the stored key, '' deletes it, other replaces it.
    chat_provider anthropic without resulting key -> VALIDATION_ERROR (details.field='anthropic.api_key');
    openai_compatible without base_url or model -> VALIDATION_ERROR (field 'openai_compatible.base_url'
    or 'openai_compatible.model'). updated_at = utcnow."""
    raise NotImplementedError("not implemented")


async def resolve_chat(session: AsyncSession) -> dict[str, Any]:
    """ChatModelConfig for job payloads: ollama -> {provider, model: ollama.chat_model,
    base_url: ollama.url, api_key: None}; anthropic -> {model, base_url: None, api_key};
    openai_compatible -> {model, base_url, api_key}."""
    raise NotImplementedError("not implemented")


async def ollama_url(session: AsyncSession) -> str:
    raise NotImplementedError("not implemented")


async def reranker_model(session: AsyncSession) -> str:
    raise NotImplementedError("not implemented")
