"""Semantic splitter (house style for components/): NLTK punkt sentences -> per-sentence
embeddings -> cosine gaps -> breakpoint groups -> one Document per group; gaps are reported
in the 'semantic' block for the artifact."""

import math
from typing import Any

import numpy as np
from haystack import Document, component
from nltk import sent_tokenize


def breakpoints(distances: list[float], percentile: int) -> tuple[float, list[bool]]:
    """threshold = numpy.percentile(distances, percentile); is_break[i] = distances[i] > threshold.
    [] -> (0.0, [])."""
    if not distances:
        return 0.0, []
    threshold = float(np.percentile(distances, percentile))
    return threshold, [d > threshold for d in distances]


def group_sentences(
    sentences: list[str], is_break: list[bool], min_sentences: int, max_sentences: int
) -> list[list[int]]:
    """Group sentence indices: start a new group after sentence i when is_break[i] and the current
    group has >= min_sentences, or when the group reached max_sentences. Every index appears once,
    in order."""
    groups: list[list[int]] = []
    current: list[int] = []
    for i in range(len(sentences)):
        current.append(i)
        if i == len(sentences) - 1:
            break
        breakable = i < len(is_break) and is_break[i]
        if len(current) >= max_sentences or (breakable and len(current) >= min_sentences):
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def _cosine(a: list[float], b: list[float]) -> float:
    """Dot product normalised by both lengths (0.0 when either vector has no mass)."""
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


def _spans(source: str, sentences: list[str]) -> list[tuple[int, int]]:
    """[start, end) of each sentence in source, searched in order from the previous match;
    (-1, -1) when a sentence is not found."""
    spans: list[tuple[int, int]] = []
    cursor = 0
    for sent in sentences:
        pos = source.find(sent, cursor)
        if pos >= 0:
            cursor = pos + len(sent)
        spans.append((pos, pos + len(sent)))
    return spans


@component
class SemanticSplitter:
    """Sentences via NLTK punkt (nltk.sent_tokenize, language english) on the single input Document;
    embed every sentence with `embedder` (a Haystack text embedder component: run(text) ->
    {'embedding'}); distance[i] = 1 - cosine(sentence i, sentence i+1); breakpoints; group; each
    group -> Document(content = joined sentence texts exactly as in the source (from first sentence
    start to last sentence end), meta split_idx_start). Also outputs the gaps for the artifact
    'semantic' block: {'threshold', 'gaps': [{'after_sentence', 'distance', 'is_break'}]}."""

    def __init__(
        self, embedder: Any, breakpoint_percentile: int, min_sentences: int, max_sentences: int
    ) -> None:
        self.embedder = embedder
        self.breakpoint_percentile = breakpoint_percentile
        self.min_sentences = min_sentences
        self.max_sentences = max_sentences

    @component.output_types(documents=list[Document], semantic=dict[str, Any])
    def run(self, documents: list[Document]) -> dict[str, Any]:
        if not documents:
            return {"documents": [], "semantic": {"threshold": 0.0, "gaps": []}}
        source = documents[0].content or ""
        sentences = sent_tokenize(source, "english")
        if not sentences:
            return {"documents": [], "semantic": {"threshold": 0.0, "gaps": []}}
        embeddings = [self.embedder.run(text=sent)["embedding"] for sent in sentences]
        distances = [
            1.0 - _cosine(embeddings[i], embeddings[i + 1]) for i in range(len(embeddings) - 1)
        ]
        threshold, is_break = breakpoints(distances, self.breakpoint_percentile)
        groups = group_sentences(sentences, is_break, self.min_sentences, self.max_sentences)
        spans = _spans(source, sentences)
        docs: list[Document] = []
        for group in groups:
            first, last = group[0], group[-1]
            start, end = spans[first][0], spans[last][1]
            content = source[start:end] if start >= 0 else " ".join(sentences[first : last + 1])
            meta: dict[str, Any] = {"split_idx_start": start if start >= 0 else None}
            docs.append(Document(content=content, meta=meta))
        gaps = [
            {"after_sentence": i, "distance": d, "is_break": is_break[i]}
            for i, d in enumerate(distances)
        ]
        return {"documents": docs, "semantic": {"threshold": threshold, "gaps": gaps}}
