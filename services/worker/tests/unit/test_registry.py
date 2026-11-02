"""Unit tests for the model registry: baked-in tokenizer loading and RealModelSet factories.
Factories must return the real Haystack components with the configured attributes, without
connecting to any model server at construction time."""

import os
import socket
from typing import Any

import pytest
from haystack.components.generators.chat import OpenAIChatGenerator
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

from rag_worker.contracts_gen.shared.common_schema import ChatModelConfig, DenseModelConfig
from rag_worker.models.registry import RealModelSet, load_tokenizer

DENSE_CFG = DenseModelConfig(model="bge-m3", dims=1024, ollama_url="http://o:11434")
OLLAMA_CHAT_CFG = ChatModelConfig(
    provider="ollama", model="qwen3:8b", base_url="http://o:11434", api_key=None
)
ANTHROPIC_CHAT_CFG = ChatModelConfig(
    provider="anthropic", model="claude-sonnet-5-5", base_url=None, api_key="k"
)
OPENAI_CHAT_CFG = ChatModelConfig(
    provider="openai_compatible", model="gpt-4.1-mini", base_url="http://g:8080/v1", api_key=None
)
SPARSE_MODEL = "Qdrant/bm25"
RANKER_MODEL = "Xenova/ms-marco-MiniLM-L-6-v2"


def test_load_tokenizer_first_tokens_and_cache() -> None:
    assert load_tokenizer("bge-m3").encode("hello world").tokens[0] == "<s>"
    assert load_tokenizer("all-minilm").encode("hi").tokens[0] == "[CLS]"
    assert load_tokenizer("bge-m3") is load_tokenizer("bge-m3")


def test_dense_document_embedder_is_ollama() -> None:
    embedder = RealModelSet().dense_document_embedder(DENSE_CFG, 8)
    assert isinstance(embedder, OllamaDocumentEmbedder)
    assert embedder.model == "bge-m3"
    assert str(embedder.url) == str(DENSE_CFG.ollama_url)
    assert embedder.batch_size == 8


def test_sparse_and_ranker_are_fastembed() -> None:
    models = RealModelSet()
    embedder = models.sparse_document_embedder(SPARSE_MODEL)
    assert isinstance(embedder, FastembedSparseDocumentEmbedder)
    assert embedder.model_name == SPARSE_MODEL
    assert embedder.cache_dir == os.environ["FASTEMBED_CACHE_PATH"]
    ranker = models.ranker(RANKER_MODEL, 3)
    assert isinstance(ranker, FastembedRanker)
    assert ranker.model_name == RANKER_MODEL
    assert ranker.top_k == 3


def test_chat_generator_ollama_kwargs() -> None:
    gen = RealModelSet().chat_generator(OLLAMA_CHAT_CFG, 0.2, 100)
    assert isinstance(gen, OllamaChatGenerator)
    assert gen.model == "qwen3:8b"
    assert str(gen.url) == str(OLLAMA_CHAT_CFG.base_url)
    assert gen.generation_kwargs == {"temperature": 0.2, "num_predict": 100}


def test_chat_generator_anthropic_and_openai() -> None:
    models = RealModelSet()
    claude = models.chat_generator(ANTHROPIC_CHAT_CFG, 0.2, 100)
    assert isinstance(claude, AnthropicChatGenerator)
    assert claude.model == "claude-sonnet-5-5"
    assert claude.api_key == Secret.from_token("k")
    assert claude.generation_kwargs == {"temperature": 0.2, "max_tokens": 100}
    gpt = models.chat_generator(OPENAI_CHAT_CFG, 0.2, 100)
    assert isinstance(gpt, OpenAIChatGenerator)
    assert gpt.model == "gpt-4.1-mini"
    assert gpt.api_key == Secret.from_token("none")
    assert str(gpt.api_base_url) == str(OPENAI_CHAT_CFG.base_url)
    assert gpt.generation_kwargs == {"temperature": 0.2, "max_tokens": 100}


def test_constructing_components_opens_no_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_socket(*args: Any, **kwargs: Any) -> socket.socket:
        raise AssertionError("socket.create_connection was called at construction time")

    monkeypatch.setattr(socket, "create_connection", no_socket)
    models = RealModelSet()
    assert isinstance(models.dense_document_embedder(DENSE_CFG, 8), OllamaDocumentEmbedder)
    assert isinstance(models.dense_text_embedder(DENSE_CFG), OllamaTextEmbedder)
    assert isinstance(
        models.sparse_document_embedder(SPARSE_MODEL), FastembedSparseDocumentEmbedder
    )
    assert isinstance(models.sparse_text_embedder(SPARSE_MODEL), FastembedSparseTextEmbedder)
    assert isinstance(models.ranker(RANKER_MODEL, 3), FastembedRanker)
    assert isinstance(models.chat_generator(OLLAMA_CHAT_CFG, 0.2, 100), OllamaChatGenerator)
    assert isinstance(models.chat_generator(ANTHROPIC_CHAT_CFG, 0.2, 100), AnthropicChatGenerator)
    assert isinstance(models.chat_generator(OPENAI_CHAT_CFG, 0.2, 100), OpenAIChatGenerator)
