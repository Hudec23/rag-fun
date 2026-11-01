"""Model factory. MODEL_BACKEND=fake -> models.fakes; real -> Ollama / fastembed / Anthropic / OpenAI.
Every factory returns a Haystack component; nothing connects to a model server at construction time."""

from collections.abc import Callable
from typing import Any, Protocol

from haystack.dataclasses import StreamingChunk
from tokenizers import Tokenizer

from rag_worker.contracts_gen.shared.common_schema import ChatModelConfig, DenseModelConfig

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


def load_tokenizer(dense_model: str) -> Tokenizer:
    """Tokenizer.from_file(hf_hub_download(repo, 'tokenizer.json')) — files are baked into the image,
    HF_HUB_OFFLINE=1. Cached per model (functools.cache)."""
    raise NotImplementedError("not implemented")


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


def build_model_set(backend: str) -> ModelSet:
    return FakeModelSet() if backend == "fake" else RealModelSet()
