---
id: T-worker-012
kind: impl
feature: F-embed
title: tokenizer loading + real model factories
service: worker
depends_on:
- T-worker-012t
edit:
- services/worker/src/rag_worker/models/registry.py
read:
- services/worker/src/rag_worker/components/chunk_annotator.py
locked:
- services/worker/tests/unit/test_registry.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check src/rag_worker/models/registry.py && uv run --frozen ruff check src/rag_worker/models/registry.py && uv run --frozen mypy src'
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_registry.py
max_attempts: 3
---

## Goal
Implement: tokenizer loading + real model factories. The tests written by T-worker-012t define done.

## Context
Unit test; tokenizer files are baked in the image (HF_HUB_OFFLINE=1). Check attributes of the returned components (e.g. `.model`, `.url`, `.top_k`, `.generation_kwargs`).

Stub in `services/worker/src/rag_worker/models/registry.py` (signatures are final; replace only the bodies that raise NotImplementedError):
```python
"""Model factory. MODEL_BACKEND=fake -> models.fakes; real -> Ollama / fastembed / Anthropic / OpenAI.
Every factory returns a Haystack component; nothing connects to a model server at construction time."""
from collections.abc import Callable
from typing import Any, Protocol
from haystack.dataclasses import StreamingChunk
from tokenizers import Tokenizer
from rag_worker.contracts_gen.shared.common_schema import ChatModelConfig, DenseModelConfig
TOKENIZERS: dict[str, tuple[str, int]] = {
    "bge-m3": ("BAAI/bge-m3", 8192),
    "nomic-embed-text": ("nomic-ai/nomic-embed-text-v1.5", 8192),
    "mxbai-embed-large": ("mixedbread-ai/mxbai-embed-large-v1", 512),
    "all-minilm": ("sentence-transformers/all-MiniLM-L6-v2", 256),
}


def load_tokenizer(dense_model: str) -> Tokenizer:
    """Tokenizer.from_file(hf_hub_download(repo, 'tokenizer.json')) — files are baked into the image,
    HF_HUB_OFFLINE=1. Cached per model (functools.cache)."""
    raise NotImplementedError("not implemented")

class RealModelSet:
    """dense: OllamaDocumentEmbedder / OllamaTextEmbedder(model=cfg.model, url=cfg.ollama_url
    [, batch_size]). sparse: FastembedSparseDocumentEmbedder / FastembedSparseTextEmbedder(model,
    cache_dir=$FASTEMBED_CACHE_PATH). ranker: FastembedRanker(model_name=model, top_k, cache_dir).
    chat: ollama -> OllamaChatGenerator(model, url=base_url, generation_kwargs={'temperature',
    'num_predict': max_tokens}); anthropic -> AnthropicChatGenerator(api_key=Secret.from_token(key),
    model, generation_kwargs={'temperature', 'max_tokens'}); openai_compatible -> OpenAIChatGenerator(
    api_key=Secret.from_token(key or 'none'), model, api_base_url=base_url, generation_kwargs={
    'temperature', 'max_tokens'}). All pass streaming_callback through."""

    backend = "real"

    def dense_document_embedder(self, cfg: DenseModelConfig, batch_size: int) -> Any:
        raise NotImplementedError("not implemented")

    def dense_text_embedder(self, cfg: DenseModelConfig) -> Any:
        raise NotImplementedError("not implemented")

    def sparse_document_embedder(self, model: str) -> Any:
        raise NotImplementedError("not implemented")

    def sparse_text_embedder(self, model: str) -> Any:
        raise NotImplementedError("not implemented")

    def ranker(self, model: str, top_k: int) -> Any:
        raise NotImplementedError("not implemented")

    def chat_generator(
        self,
        cfg: ChatModelConfig,
        temperature: float,
        max_tokens: int,
        streaming_callback: Callable[[StreamingChunk], None] | None = None,
    ) -> Any:
        raise NotImplementedError("not implemented")

    def tokenizer(self, dense_model: str) -> Tokenizer:
        return load_tokenizer(dense_model)
```

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, anything under contracts/ or .autospec/plan/, pyproject.toml or uv.lock.
- Do not add dependencies or change signatures of existing functions/classes.
- Do not catch broad exceptions to hide failures; raise the documented AppError/WorkerError codes.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
