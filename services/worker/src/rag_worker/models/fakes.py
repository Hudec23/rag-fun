"""Deterministic, offline stand-ins for every model (MODEL_BACKEND=fake; used by all tests and e2e).

Dense: hashed bag-of-words (each lowercase word -> dim sha1(word) % dims), L2-normalised, so cosine
similarity reflects word overlap. Sparse: same hashing into 2**20 indices, values = counts.
Ranker: score = |query words ∩ doc words| / (1 + |query words|). Chat: fixed reply that cites [1]."""

import dataclasses
import hashlib
import math
import re
from collections import Counter
from collections.abc import Callable
from typing import Any

from haystack import Document, component
from haystack.dataclasses import ChatMessage, SparseEmbedding, StreamingChunk

WORD = re.compile(r"[a-z0-9]+")
SPARSE_SPACE = 2**20


def words(text: str) -> list[str]:
    return WORD.findall(text.lower())


def _bucket(word: str, size: int) -> int:
    return int(hashlib.sha1(word.encode()).hexdigest(), 16) % size


def fake_dense(text: str, dims: int) -> list[float]:
    vec = [0.0] * dims
    for w in words(text):
        vec[_bucket(w, dims)] += 1.0
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        vec[0] = 1.0
        return vec
    return [round(v / norm, 6) for v in vec]


def fake_sparse(text: str) -> SparseEmbedding:
    counts = Counter(_bucket(w, SPARSE_SPACE) for w in words(text))
    indices = sorted(counts)
    return SparseEmbedding(indices=indices, values=[float(counts[i]) for i in indices])


@component
class FakeDenseDocumentEmbedder:
    def __init__(self, dims: int) -> None:
        self.dims = dims

    @component.output_types(documents=list[Document])
    def run(self, documents: list[Document]) -> dict[str, Any]:
        out = [
            dataclasses.replace(d, embedding=fake_dense(d.content or "", self.dims))
            for d in documents
        ]
        return {"documents": out}


@component
class FakeDenseTextEmbedder:
    def __init__(self, dims: int) -> None:
        self.dims = dims

    @component.output_types(embedding=list[float])
    def run(self, text: str) -> dict[str, Any]:
        return {"embedding": fake_dense(text, self.dims)}


@component
class FakeSparseDocumentEmbedder:
    @component.output_types(documents=list[Document])
    def run(self, documents: list[Document]) -> dict[str, Any]:
        out = [
            dataclasses.replace(d, sparse_embedding=fake_sparse(d.content or "")) for d in documents
        ]
        return {"documents": out}


@component
class FakeSparseTextEmbedder:
    @component.output_types(sparse_embedding=SparseEmbedding)
    def run(self, text: str) -> dict[str, Any]:
        return {"sparse_embedding": fake_sparse(text)}


@component
class FakeRanker:
    def __init__(self, top_k: int = 10) -> None:
        self.top_k = top_k

    @component.output_types(documents=list[Document])
    def run(
        self, query: str, documents: list[Document], top_k: int | None = None
    ) -> dict[str, Any]:
        q = set(words(query))
        scored = []
        for i, doc in enumerate(documents):
            overlap = len(q & set(words(doc.content or "")))
            scored.append((-(overlap / (1 + len(q))), i, doc))
        scored.sort(key=lambda t: (t[0], t[1]))
        out = []
        for neg, _, doc in scored[: top_k or self.top_k]:
            out.append(dataclasses.replace(doc, score=round(-neg, 6)))
        return {"documents": out}


def fake_reply(messages: list[ChatMessage]) -> str:
    """'Fake answer to: <first line of the last user message, max 200 chars> [1]'."""
    user = [m for m in messages if m.role.value == "user"]
    first = (user[-1].text or "").strip().splitlines()[0][:200] if user and user[-1].text else ""
    return f"Fake answer to: {first} [1]"


@component
class FakeChatGenerator:
    def __init__(self, streaming_callback: Callable[[StreamingChunk], None] | None = None) -> None:
        self.streaming_callback = streaming_callback

    @component.output_types(replies=list[ChatMessage])
    def run(self, messages: list[ChatMessage]) -> dict[str, Any]:
        text = fake_reply(messages)
        if self.streaming_callback is not None:
            parts = text.split(" ")
            for i, part in enumerate(parts):
                piece = part if i == len(parts) - 1 else part + " "
                self.streaming_callback(StreamingChunk(content=piece))
        prompt_words = sum(len(words(m.text or "")) for m in messages)
        reply = ChatMessage.from_assistant(
            text,
            meta={"usage": {"prompt_tokens": prompt_words, "completion_tokens": len(words(text))}},
        )
        return {"replies": [reply]}
