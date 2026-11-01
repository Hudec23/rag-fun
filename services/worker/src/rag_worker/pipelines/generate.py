from collections.abc import Callable
from typing import Any

from haystack import Pipeline
from haystack.dataclasses import StreamingChunk

from rag_worker.contracts_gen.shared.common_schema import ChatModelConfig
from rag_worker.models.registry import ModelSet


def build_generate_pipeline(
    chat: ChatModelConfig,
    temperature: float,
    max_tokens: int,
    models: ModelSet,
    streaming_callback: Callable[[StreamingChunk], None] | None,
) -> Pipeline:
    """'prompt' = ChatPromptBuilder([system prompts.ANSWER_SYSTEM, user prompts.ANSWER_USER],
    required_variables='*') -> 'llm' = models.chat_generator(chat, temperature, max_tokens,
    streaming_callback)."""
    raise NotImplementedError("not implemented")


def generate_artifact(
    chat: ChatModelConfig,
    messages: list[dict[str, str]],
    budget: dict[str, int],
    context: list[dict[str, Any]],
    answer: str,
    usage: dict[str, int | None],
) -> dict[str, Any]:
    """contracts/artifacts/generate.schema.json; citations = context_builder.parse_citations(answer,
    len(context))."""
    raise NotImplementedError("not implemented")
