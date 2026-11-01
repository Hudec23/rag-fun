from typing import Any

from haystack import Pipeline

from rag_worker.contracts_gen.shared.common_schema import ChatModelConfig
from rag_worker.models.registry import ModelSet


def build_transform_pipeline(strategy: str, chat: ChatModelConfig, models: ModelSet) -> Pipeline:
    """'prompt' = ChatPromptBuilder(template=[system (prompts.*_SYSTEM by strategy), user
    '{{ question }}'], required_variables='*') -> 'llm' = models.chat_generator(chat, temperature 0.2,
    max_tokens 400) (prompt.prompt -> llm.messages). strategy 'none' -> ValueError (not built)."""
    raise NotImplementedError("not implemented")


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
    raise NotImplementedError("not implemented")
