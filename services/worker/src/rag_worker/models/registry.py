"""Model factory. MODEL_BACKEND=fake -> models.fakes; real -> Ollama / fastembed / Anthropic / OpenAI.
Every factory returns a Haystack component; nothing connects to a model server at construction time."""

import functools
import os
from collections.abc import Callable
from typing import Any, Protocol, cast

from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import StreamingChunk
from haystack.utils import Secret
from haystack_integrations.components.embedders.fastembed import (
    FastembedSparseDocumentEmbedder,
    FastembedSparseTextEmbedder,
)
from haystack_integrations.components.embedders.ollama import (
    OllamaDocumentEmbedder,
    OllamaTextEmbedder,
)
from haystack_integrations.components.generators.anthropic import AnthropicChatGenerator
from haystack_integrations.components.generators.ollama import OllamaChatGenerator
from haystack_integrations.components.rankers.fastembed import FastembedRanker
from huggingface_hub import hf_hub_download
from tokenizers import Tokenizer

from rag_worker.contracts_gen.shared.common_schema import ChatModelConfig, DenseModelConfig
from rag_worker.errors import WorkerError

# dense model -> (HF repo of its tokenizer.json, max_tokens)  (contracts/artifacts/embed.schema.json)
TOKENIZERS: dict[str, tuple[str, int]] = {
    "bge-m3": ("BAAI/bge-m3", 8192),
    "nomic-embed-text": ("nomic-ai/nomic-embed-text-v1.5", 8192),
    "mxbai-embed-large": ("mixedbread-ai/mxbai-embed-large-v1", 512),
    "all-minilm": ("sentence-transformers/all-MiniLM-L6-v2", 256),
}


class ModelSet(Protocol):
    backend: str

    def dense_document_embedder(self, cfg: DenseModelConfig, batch_size: int) -> Any: ...
    def dense_text_embedder(self, cfg: DenseModelConfig) -> Any: ...
    def sparse_document_embedder(self, model: str) -> Any: ...
    def sparse_text_embedder(self, model: str) -> Any: ...
    def ranker(self, model: str, top_k: int) -> Any: ...
    def chat_generator(
        self,
        cfg: ChatModelConfig,
        temperature: float,
        max_tokens: int,
        streaming_callback: Callable[[StreamingChunk], None] | None = None,
    ) -> Any: ...
    def tokenizer(self, dense_model: str) -> Tokenizer: ...


@functools.cache
def load_tokenizer(dense_model: str) -> Tokenizer:
    """Tokenizer.from_file(hf_hub_download(repo, 'tokenizer.json')) — files are baked into the image,
    HF_HUB_OFFLINE=1. Cached per model (functools.cache)."""
    entry = TOKENIZERS.get(dense_model)
    if entry is None:
        raise WorkerError("MODEL_NOT_AVAILABLE", details={"model": dense_model})
    repo, _max_tokens = entry
    return Tokenizer.from_file(cast(str, hf_hub_download(repo, "tokenizer.json")))


class FakeModelSet:
    """Implemented: returns models.fakes components; tokenizers are the real baked ones."""

    backend = "fake"

    def dense_document_embedder(self, cfg: DenseModelConfig, batch_size: int) -> Any:
        from rag_worker.models.fakes import FakeDenseDocumentEmbedder

        return FakeDenseDocumentEmbedder(cfg.dims)

    def dense_text_embedder(self, cfg: DenseModelConfig) -> Any:
        from rag_worker.models.fakes import FakeDenseTextEmbedder

        return FakeDenseTextEmbedder(cfg.dims)

    def sparse_document_embedder(self, model: str) -> Any:
        from rag_worker.models.fakes import FakeSparseDocumentEmbedder

        return FakeSparseDocumentEmbedder()

    def sparse_text_embedder(self, model: str) -> Any:
        from rag_worker.models.fakes import FakeSparseTextEmbedder

        return FakeSparseTextEmbedder()

    def ranker(self, model: str, top_k: int) -> Any:
        from rag_worker.models.fakes import FakeRanker

        return FakeRanker(top_k)

    def chat_generator(
        self,
        cfg: ChatModelConfig,
        temperature: float,
        max_tokens: int,
        streaming_callback: Callable[[StreamingChunk], None] | None = None,
    ) -> Any:
        from rag_worker.models.fakes import FakeChatGenerator

        return FakeChatGenerator(streaming_callback)

    def tokenizer(self, dense_model: str) -> Tokenizer:
        return load_tokenizer(dense_model)


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
        return OllamaDocumentEmbedder(
            model=cfg.model, url=str(cfg.ollama_url), batch_size=batch_size
        )

    def dense_text_embedder(self, cfg: DenseModelConfig) -> Any:
        return OllamaTextEmbedder(model=cfg.model, url=str(cfg.ollama_url))

    def sparse_document_embedder(self, model: str) -> Any:
        return FastembedSparseDocumentEmbedder(
            model=model, cache_dir=os.environ["FASTEMBED_CACHE_PATH"]
        )

    def sparse_text_embedder(self, model: str) -> Any:
        return FastembedSparseTextEmbedder(
            model=model, cache_dir=os.environ["FASTEMBED_CACHE_PATH"]
        )

    def ranker(self, model: str, top_k: int) -> Any:
        return FastembedRanker(
            model_name=model, top_k=top_k, cache_dir=os.environ["FASTEMBED_CACHE_PATH"]
        )

    def chat_generator(
        self,
        cfg: ChatModelConfig,
        temperature: float,
        max_tokens: int,
        streaming_callback: Callable[[StreamingChunk], None] | None = None,
    ) -> Any:
        if cfg.provider == "ollama":
            if cfg.base_url is None:
                raise WorkerError("MODEL_NOT_AVAILABLE", details={"model": cfg.model})
            return OllamaChatGenerator(
                model=cfg.model,
                url=str(cfg.base_url),
                generation_kwargs={"temperature": temperature, "num_predict": max_tokens},
                streaming_callback=streaming_callback,
            )
        if cfg.provider == "anthropic":
            return AnthropicChatGenerator(
                api_key=Secret.from_token(cfg.api_key or "none"),
                model=cfg.model,
                generation_kwargs={"temperature": temperature, "max_tokens": max_tokens},
                streaming_callback=streaming_callback,
            )
        return OpenAIChatGenerator(
            api_key=Secret.from_token(cfg.api_key or "none"),
            model=cfg.model,
            api_base_url=str(cfg.base_url) if cfg.base_url is not None else None,
            generation_kwargs={"temperature": temperature, "max_tokens": max_tokens},
            streaming_callback=streaming_callback,
        )

    def tokenizer(self, dense_model: str) -> Tokenizer:
        return load_tokenizer(dense_model)


def build_model_set(backend: str) -> ModelSet:
    return FakeModelSet() if backend == "fake" else RealModelSet()
