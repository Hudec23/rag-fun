"""Transform pipeline + artifact: build_transform_pipeline assembles the Haystack pipeline
('prompt' -> 'llm') per strategy, transform_artifact normalizes the chat reply to
contracts/artifacts/transform.schema.json."""

import re
from typing import Any

from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.dataclasses import ChatMessage

from rag_worker.contracts_gen.shared.common_schema import ChatModelConfig
from rag_worker.errors import WorkerError
from rag_worker.models.registry import ModelSet
from rag_worker.pipelines.prompts import HYDE_SYSTEM, MULTI_QUERY_SYSTEM, REWRITE_SYSTEM

# prompts.*_SYSTEM by strategy (the user template '{{ question }}' is shared)
_SYSTEM_PROMPTS: dict[str, str] = {
    "rewrite": REWRITE_SYSTEM,
    "multi_query": MULTI_QUERY_SYSTEM,
    "hyde": HYDE_SYSTEM,
}
# '- ', '*', '+ ', '1. ', '2) ' style list markers the LLM may still prepend
_QUERY_PREFIX = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")


class TransformPipeline(Pipeline):
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


def build_transform_pipeline(strategy: str, chat: ChatModelConfig, models: ModelSet) -> Pipeline:
    """'prompt' = ChatPromptBuilder(template=[system (prompts.*_SYSTEM by strategy), user
    '{{ question }}'], required_variables='*') -> 'llm' = models.chat_generator(chat, temperature 0.2,
    max_tokens 400) (prompt.prompt -> llm.messages). strategy 'none' -> ValueError (not built)."""
    system = _SYSTEM_PROMPTS.get(strategy)
    if system is None:
        raise ValueError(f"cannot build a transform pipeline for strategy {strategy!r}")
    pipeline = TransformPipeline()
    pipeline.add_component(
        "prompt",
        ChatPromptBuilder(
            template=[ChatMessage.from_system(system), ChatMessage.from_user("{{ question }}")],
            required_variables="*",
        ),
    )
    pipeline.add_component("llm", models.chat_generator(chat, 0.2, 400))
    pipeline.connect("prompt.prompt", "llm.messages")
    return pipeline


def transform_artifact(
    strategy: str,
    question: str,
    reply: str | None,
    messages: list[dict[str, str]],
    chat: ChatModelConfig | None,
    num_queries: int,
) -> dict[str, Any]:
    """contracts/artifacts/transform.schema.json. none -> queries [question], messages [], model None.
    rewrite -> [first non-empty reply line stripped] (empty reply -> [question]). multi_query ->
    [question] + up to num_queries distinct non-empty reply lines (stripped of '- ', '1. ' style
    prefixes, excluding lines equal to question). hyde -> queries [reply.strip()], hyde_document same."""
    queries: list[str]
    hyde_document: str | None
    prompt_messages: list[dict[str, str]]
    if strategy == "none":
        queries, hyde_document, prompt_messages = [question], None, []
    elif strategy == "rewrite":
        first = next(
            (line.strip() for line in (reply or "").splitlines() if line.strip()), question
        )
        queries, hyde_document, prompt_messages = [first], None, messages
    elif strategy == "multi_query":
        limit = 1 + min(num_queries, 5)  # schema: queries maxItems 6 (question + up to 5)
        queries = [question]
        seen = {question}
        for line in (reply or "").splitlines():
            line = _QUERY_PREFIX.sub("", line).strip()
            if not line or line in seen:
                continue
            seen.add(line)
            queries.append(line)
            if len(queries) >= limit:
                break
        hyde_document, prompt_messages = None, messages
    elif strategy == "hyde":
        text = (reply or "").strip()
        queries, hyde_document, prompt_messages = [text or question], text or None, messages
    else:
        raise WorkerError("UNSUPPORTED_FOR_STRATEGY", details={"strategy": strategy})

    model: dict[str, str] | None = None
    if strategy != "none" and chat is not None:
        model = {"provider": chat.provider, "model": chat.model}
    return {
        "schema_version": 1,
        "stage": "transform",
        "strategy": strategy,
        "question": question,
        "queries": queries,
        "hyde_document": hyde_document,
        "messages": prompt_messages,
        "model": model,
    }
