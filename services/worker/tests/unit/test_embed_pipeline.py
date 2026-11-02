"""Unit tests for the embed pipeline + embed artifact (services/worker/src/rag_worker/pipelines/embed.py):
build/run the 'dense' -> 'sparse' -> 'tokens' pipeline over inline Documents (FakeModelSet), and check
embed_artifact output against contracts/artifacts/embed.schema.json. The module is a stub raising
NotImplementedError, so every test here is red until T-worker-024 lands."""

from haystack import Document, Pipeline

from rag_worker.contracts_gen.shared.common_schema import CollectionRef, DenseModelConfig
from rag_worker.models.fakes import fake_dense, fake_sparse
from rag_worker.models.registry import FakeModelSet
from rag_worker.pipelines.embed import build_embed_pipeline, embed_artifact
from tests.contract import errors

FILE_ID = "019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a01"
COLLECTION = CollectionRef(
    id="019a4b2c-1d00-7b00-8000-0000000000aa",
    qdrant_name="rf_019a4b2c1d007b0080000000000000aa",
    dense=DenseModelConfig(model="all-minilm", dims=384, ollama_url="http://x"),
    sparse_model="Qdrant/bm25",
)
TOKENIZER_REPO = "sentence-transformers/all-MiniLM-L6-v2"
DOCS = [
    Document(
        content="Q3 revenue grew 12 percent",
        id=f"{FILE_ID}:00000",
        meta={"doc_id": f"{FILE_ID}:00000"},
    ),
    Document(
        content="Margins held steady against guidance",
        id=f"{FILE_ID}:00001",
        meta={"doc_id": f"{FILE_ID}:00001"},
    ),
    Document(
        content="Scan of the invoice totals forty dollars",
        id=f"{FILE_ID}:00002",
        meta={"doc_id": f"{FILE_ID}:00002"},
    ),
]


def _pipeline() -> Pipeline:
    return build_embed_pipeline(COLLECTION, 16, FakeModelSet())


def _embedded() -> list[Document]:
    out = _pipeline().run({"dense": {"documents": DOCS}})
    return out["tokens"]["documents"]


def test_run_yields_embedding_sparse_and_token_meta() -> None:
    docs = _embedded()
    assert [d.meta["doc_id"] for d in docs] == [d.meta["doc_id"] for d in DOCS]
    for doc in docs:
        assert doc.embedding == fake_dense(doc.content, 384)
        expected = fake_sparse(doc.content)
        assert doc.sparse_embedding is not None
        assert doc.sparse_embedding.indices == expected.indices
        assert doc.sparse_embedding.values == expected.values
        assert isinstance(doc.meta["token_count"], int)
        assert doc.meta["token_count"] == len(doc.meta["tokens"])
        assert doc.meta["token_count"] > 0
        assert doc.meta["over_limit"] is False


def test_artifact_validates_against_embed_schema() -> None:
    artifact = embed_artifact(_embedded(), COLLECTION, TOKENIZER_REPO, 256)
    assert errors(artifact, "artifacts/embed.schema.json") == []
    assert artifact["schema_version"] == 1
    assert artifact["stage"] == "embed"
    assert artifact["dense_model"] == "all-minilm"
    assert artifact["dense_dims"] == 384
    assert artifact["max_tokens"] == 256
    assert artifact["sparse_model"] == "Qdrant/bm25"
    assert artifact["tokenizer"] == TOKENIZER_REPO
    assert [chunk["index"] for chunk in artifact["chunks"]] == [0, 1, 2]
    assert [chunk["doc_id"] for chunk in artifact["chunks"]] == [doc.meta["doc_id"] for doc in DOCS]


def test_three_chunks_sample_no_umap() -> None:
    artifact = embed_artifact(_embedded(), COLLECTION, TOKENIZER_REPO, 256)
    assert artifact["sample_indices"] == [0, 1, 2]
    similarity = artifact["similarity"]
    assert len(similarity) == 3
    for i, row in enumerate(similarity):
        assert len(row) == 3
        assert row[i] == 1.0
    projections = artifact["projections"]
    assert len(projections["pca2"]) == 3
    assert all(len(row) == 2 for row in projections["pca2"])
    assert len(projections["pca3"]) == 3
    assert all(len(row) == 3 for row in projections["pca3"])
    assert projections["umap2"] is None
    assert projections["umap3"] is None


def test_twelve_chunks_get_umap_projections() -> None:
    docs = [
        Document(
            content=f"Document number {i} covers topic {i} in depth",
            id=f"{FILE_ID}:{i:05d}",
            meta={"doc_id": f"{FILE_ID}:{i:05d}"},
        )
        for i in range(12)
    ]
    out = _pipeline().run({"dense": {"documents": docs}})
    artifact = embed_artifact(out["tokens"]["documents"], COLLECTION, TOKENIZER_REPO, 256)
    assert artifact["sample_indices"] == list(range(12))
    umap2 = artifact["projections"]["umap2"]
    umap3 = artifact["projections"]["umap3"]
    assert umap2 is not None
    assert umap3 is not None
    assert len(umap2) == 12
    assert all(len(row) == 2 for row in umap2)
    assert len(umap3) == 12
    assert all(len(row) == 3 for row in umap3)
    assert len(artifact["similarity"]) == 12
    assert all(len(row) == 12 for row in artifact["similarity"])


def test_dense_values_rounded_to_six_decimals() -> None:
    artifact = embed_artifact(_embedded(), COLLECTION, TOKENIZER_REPO, 256)
    for chunk in artifact["chunks"]:
        assert all(value == round(value, 6) for value in chunk["dense"])
        assert all(value == round(value, 6) for value in chunk["sparse"]["values"])


def test_pipeline_graph_names_dense_sparse_tokens() -> None:
    pipeline = build_embed_pipeline(COLLECTION, 16, FakeModelSet())
    assert set(pipeline.to_dict()["components"]) == {"dense", "sparse", "tokens"}
