"""Generate pipeline + artifact: build_generate_pipeline assembles the 'prompt' -> 'llm' Haystack
pipeline (ChatPromptBuilder over prompts.ANSWER_SYSTEM/ANSWER_USER -> chat generator from ModelSet);
generate_artifact builds contracts/artifacts/generate.schema.json with citations parsed from the
answer against the included context."""

from collections.abc import Callable
from typing import Any

from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.core.serialization import default_to_dict
from haystack.dataclasses import ChatMessage, StreamingChunk

from rag_worker.components.context_builder import parse_citations
from rag_worker.contracts_gen.shared.common_schema import ChatModelConfig
from rag_worker.models.registry import ModelSet
from rag_worker.pipelines.prompts import ANSWER_SYSTEM, ANSWER_USER


class GeneratePipeline(Pipeline):
    """'prompt' -> 'llm' pipeline whose run keeps the 'prompt' and 'llm' outputs and unwraps
    out['prompt'] to the ChatMessage list ([system, user])."""

    def run(
        self, data: dict[str, Any], include_outputs_from: set[str] | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        if include_outputs_from is None:
            include_outputs_from = {"prompt", "llm"}
        out = super().run(data, include_outputs_from=include_outputs_from, **kwargs)
        prompt = out.get("prompt")
        if isinstance(prompt, dict):
            out["prompt"] = prompt.get("prompt")
        return out


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
    pipeline = GeneratePipeline()
    pipeline.add_component(
        "prompt",
        ChatPromptBuilder(
            template=[
                ChatMessage.from_system(ANSWER_SYSTEM),
                ChatMessage.from_user(ANSWER_USER),
            ],
            required_variables="*",
        ),
    )
    llm = models.chat_generator(chat, temperature, max_tokens, streaming_callback)
    if streaming_callback is not None:
        # streaming_callback is a function, not serializable by haystack: primitives only
        # (default_to_dict shape)
        llm.to_dict = lambda: default_to_dict(llm, streaming_callback=None)
    pipeline.add_component("llm", llm)
    pipeline.connect("prompt.prompt", "llm.messages")
    return pipeline


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
    return {
        "schema_version": 1,
        "stage": "generate",
        "model": {"provider": chat.provider, "model": chat.model},
        "messages": messages,
        "budget": budget,
        "context": context,
        "answer": answer,
        "citations": parse_citations(answer, len(context)),
        "usage": usage,
    }
