from typing import Any

from haystack import Document, component


def breakpoints(distances: list[float], percentile: int) -> tuple[float, list[bool]]:
    """threshold = numpy.percentile(distances, percentile); is_break[i] = distances[i] > threshold.
    [] -> (0.0, [])."""
    raise NotImplementedError("not implemented")


def group_sentences(
    sentences: list[str], is_break: list[bool], min_sentences: int, max_sentences: int
) -> list[list[int]]:
    """Group sentence indices: start a new group after sentence i when is_break[i] and the current
    group has >= min_sentences, or when the group reached max_sentences. Every index appears once,
    in order."""
    raise NotImplementedError("not implemented")


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
        raise NotImplementedError("not implemented")
