"""F-pipeline-graph (R-019)."""

import httpx

from conftest import assert_valid


def test_every_variant_reported(api: httpx.Client) -> None:
    items = api.get("/pipeline-graphs").json()["items"]
    keys = [(g["stage"], g["variant"]) for g in items]
    assert len(keys) == 19
    assert keys[0] == ("parse", "docling_layout") and keys[-1] == ("generate", "default")
    for g in items:
        assert_valid(g, "shared/pipeline-graph.schema.json")
    sem = api.get("/pipeline-graphs/chunk/semantic").json()
    assert any(n["custom"] and n["type"].endswith("SemanticSplitter") for n in sem["nodes"])
    assert {"sender": "splitter", "receiver": "annotator"}.items() <= sem["edges"][0].items()
    hyb = api.get("/pipeline-graphs/retrieve/hybrid").json()
    assert {"dense_retriever", "sparse_retriever"} <= {n["name"] for n in hyb["nodes"]}


def test_unknown_graph_404(api: httpx.Client) -> None:
    r = api.get("/pipeline-graphs/chunk/nope")
    assert r.status_code == 404 and r.json()["error"]["code"] == "PIPELINE_GRAPH_NOT_FOUND"
