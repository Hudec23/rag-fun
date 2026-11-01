from typing import Annotated, Literal

from pydantic import Field

from rag_api.contracts_gen.shared.common_schema import ChatProvider, RerankModel
from rag_api.schemas.base import Model, Timestamp

Url = Annotated[str, Field(pattern=r"^https?://", max_length=500)]
ModelName = Annotated[str, Field(min_length=1, max_length=200)]
ApiKey = Annotated[str, Field(max_length=500)]


class OllamaSettings(Model):
    url: Url
    chat_model: ModelName


class AnthropicSettingsOut(Model):
    model: str
    api_key_set: bool
    api_key_masked: str | None


class OpenAICompatSettingsOut(Model):
    base_url: str | None
    model: str | None
    api_key_set: bool
    api_key_masked: str | None


class SettingsOut(Model):
    chat_provider: ChatProvider
    ollama: OllamaSettings
    anthropic: AnthropicSettingsOut
    openai_compatible: OpenAICompatSettingsOut
    reranker_model: RerankModel
    updated_at: Timestamp


class AnthropicSettingsIn(Model):
    model: ModelName
    api_key: ApiKey | None  # null = keep stored, "" = delete stored


class OpenAICompatSettingsIn(Model):
    base_url: Url | None
    model: Annotated[str, Field(max_length=200)] | None
    api_key: ApiKey | None


class SettingsUpdate(Model):
    chat_provider: ChatProvider
    ollama: OllamaSettings
    anthropic: AnthropicSettingsIn
    openai_compatible: OpenAICompatSettingsIn
    reranker_model: RerankModel


class ConnectionOverride(Model):
    base_url: Url | None
    api_key: ApiKey | None


class TestConnectionRequest(Model):
    target: ChatProvider
    override: ConnectionOverride | None = None


class TestConnectionResult(Model):
    target: ChatProvider
    ok: bool
    latency_ms: int
    detail: str | None
    models: list[str]


class DenseCatalogEntry(Model):
    model: str
    dims: int
    max_tokens: int
    installed: bool


class ModelCatalog(Model):
    ollama_reachable: bool
    ollama_installed: list[str]
    dense: list[DenseCatalogEntry]
    sparse: list[str]
    rerank: list[str]


ProviderName = Literal["ollama", "anthropic", "openai_compatible"]
