from haystack import Document
from haystack.dataclasses import ChatMessage, StreamingChunk

from rag_worker.models.fakes import (
    FakeChatGenerator,
    FakeDenseDocumentEmbedder,
    FakeDenseTextEmbedder,
    FakeRanker,
    FakeSparseTextEmbedder,
    fake_dense,
)


def _cos(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def test_dense_is_deterministic_normalised_and_sized() -> None:
    v = fake_dense("Revenue grew in Q3", 384)
    assert v == fake_dense("revenue GREW in q3", 384)
    assert len(v) == 384
    assert abs(sum(x * x for x in v) - 1.0) < 1e-5


def test_dense_similarity_follows_word_overlap() -> None:
    q = FakeDenseTextEmbedder(1024).run("revenue growth")["embedding"]
    near = fake_dense("revenue growth was strong", 1024)
    far = fake_dense("the cat sat on the mat", 1024)
    assert _cos(q, near) > _cos(q, far)


def test_dense_empty_text_is_unit_vector() -> None:
    assert fake_dense("", 8) == [1.0, 0, 0, 0, 0, 0, 0, 0]


def test_document_embedder_sets_embeddings() -> None:
    docs = FakeDenseDocumentEmbedder(768).run([Document(content="a b"), Document(content="c")])[
        "documents"
    ]
    assert [len(d.embedding or []) for d in docs] == [768, 768]


def test_sparse_counts_words() -> None:
    sp = FakeSparseTextEmbedder().run("tax tax refund")["sparse_embedding"]
    assert sorted(sp.values) == [1.0, 2.0]
    assert sp.indices == sorted(sp.indices)


def test_ranker_orders_by_overlap_and_truncates() -> None:
    docs = [Document(content="cats"), Document(content="tax refund rules"), Document(content="tax")]
    out = FakeRanker(top_k=2).run(query="tax refund", documents=docs)["documents"]
    assert [d.content for d in out] == ["tax refund rules", "tax"]
    assert out[0].score == round(2 / 3, 6)


def test_chat_generator_reply_and_streaming() -> None:
    chunks: list[str] = []

    def cb(c: StreamingChunk) -> None:
        chunks.append(c.content)

    out = FakeChatGenerator(cb).run(
        [ChatMessage.from_system("s"), ChatMessage.from_user("Why?\nmore")]
    )
    reply = out["replies"][0]
    assert reply.text == "Fake answer to: Why? [1]"
    assert "".join(chunks) == reply.text
    assert reply.meta["usage"]["completion_tokens"] == 5
