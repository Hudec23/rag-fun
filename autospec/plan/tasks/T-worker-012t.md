---
id: T-worker-012t
kind: test
feature: F-embed
title: 'Write tests: tokenizer loading + real model factories'
service: worker
depends_on: []
edit:
- services/worker/tests/unit/test_registry.py
read:
- services/worker/tests/unit/test_chunk_annotator.py
verify:
- docker compose -f docker-compose.dev.yml run --rm worker-dev sh -c 'uv run --frozen ruff format --check tests/unit/test_registry.py && uv run --frozen ruff check tests/unit/test_registry.py && uv run --frozen pytest -q --collect-only tests/unit/test_registry.py'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm worker-dev uv run --frozen pytest -q tests/unit/test_registry.py
max_attempts: 3
---

## Goal
Write unit tests for: tokenizer loading + real model factories. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-worker-012 implements it.

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

Fixtures (services/worker/tests/conftest.py): `ctx` (job context: settings, store = FakeObjectStore (`.objects[(bucket, key)] = bytes`), api = FakeApi (`.started`, `.results`, `.graphs`, `.calls`), events = FakePublisher (`.events`, `.types()`, shares `.calls` with api for ordering), models = FakeModelSet, qdrant_url, running = 0), `frozen_now` (ids.utcnow() == 2026-11-01T18:22:05.123Z). Paths: `tests.conftest.FIXTURES` (contract JSON fixtures, e.g. artifact_parse.json), `tests.conftest.SAMPLES` (sample files: q3-report.pdf, handbook.md, notes.txt, prices.csv, contract.docx, budget.xlsx, faq.html, scan-invoice.png). Contract validation: `from tests.contract import errors` → `errors(obj, 'artifacts/chunk.schema.json') == []`. Fake models: models.fakes (`fake_dense(text, dims)`, `fake_sparse(text)`, FakeRanker, FakeChatGenerator reply 'Fake answer to: <first line of last user message> [1]').

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (fixtures, naming `test_<behaviour>`, exact asserts).
1. load_tokenizer('bge-m3').encode('hello world').tokens[0] == '<s>'; load_tokenizer('all-minilm').encode('hi').tokens[0] == '[CLS]'; same object returned twice (cached)
2. RealModelSet().dense_document_embedder(DenseModelConfig(model='bge-m3', dims=1024, ollama_url='http://o:11434'), 8) is an OllamaDocumentEmbedder with model 'bge-m3', url 'http://o:11434', batch_size 8
3. sparse_document_embedder('Qdrant/bm25') is a FastembedSparseDocumentEmbedder with model 'Qdrant/bm25'; ranker('Xenova/ms-marco-MiniLM-L-6-v2', 3) is a FastembedRanker with top_k 3
4. chat_generator(ollama cfg, 0.2, 100) → OllamaChatGenerator, generation_kwargs {'temperature': 0.2, 'num_predict': 100}
5. chat_generator(anthropic cfg with api_key 'k', ...) → AnthropicChatGenerator; openai_compatible cfg → OpenAIChatGenerator with api_base_url == base_url
6. no network: constructing every component does not open a socket (use the conftest-free check: monkeypatch socket.create_connection to raise)

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
