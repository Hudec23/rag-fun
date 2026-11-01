import sys
sys.path.insert(0, ".")
import core
from core import TASKS, feature, finalize
import spec_api, spec_worker, spec_web  # noqa: F401  (register tasks)

A = "services/web/tests/acceptance/"
E = "tests/e2e/"
feature("F-upload", "Upload files in batches with tags", ["R-001", "R-002", "R-003"], ["contracts/openapi/api.yaml"], [E + "test_upload.py", A + "Upload.test.tsx"])
feature("F-collections", "Manage collections", ["R-012"], ["contracts/openapi/api.yaml", "contracts/jobs/drop_collection.schema.json"], [E + "test_collections.py", A + "Collections.test.tsx"])
feature("F-one-command", "Preconfigured one-command start (bootstrap)", ["R-025"], ["contracts/openapi/api.yaml"], [E + "test_bootstrap.py"])
feature("F-status", "Service status bar", ["R-024"], ["contracts/openapi/api.yaml", "contracts/events/worker.heartbeat.schema.json"], [E + "test_status.py", A + "StatusBar.test.tsx"])
feature("F-stage-flow", "Step-by-step stages, versions, stale, run-all", ["R-013"], ["contracts/openapi/api.yaml", "contracts/openapi/internal.yaml", "contracts/jobs/parse.schema.json"], [E + "test_stage_flow.py", A + "IngestRun.test.tsx"])
feature("F-live-progress", "Live progress over SSE", ["R-014"], ["contracts/events/stage.progress.schema.json", "contracts/events/run.updated.schema.json"], [E + "test_events.py"])
feature("F-parse", "Parse strategies + page/bbox view", ["R-004", "R-005"], ["contracts/artifacts/parse.schema.json"], [E + "test_parse.py", A + "ParseView.test.tsx"])
feature("F-chunk", "Chunk strategies + chunk view", ["R-006", "R-007"], ["contracts/artifacts/chunk.schema.json"], [E + "test_chunk.py", A + "ChunkView.test.tsx"])
feature("F-embed", "Embeddings inspected before storing", ["R-008", "R-009"], ["contracts/artifacts/embed.schema.json"], [E + "test_embed.py", A + "EmbedView.test.tsx"])
feature("F-store", "Store in Qdrant with payload tags", ["R-010", "R-003"], ["contracts/artifacts/store.schema.json", "contracts/qdrant/payload.schema.json"], [E + "test_store.py", E + "test_tags.py", A + "StoreView.test.tsx"])
feature("F-qdrant-browser", "Qdrant browser with filters", ["R-011"], ["contracts/openapi/api.yaml", "contracts/qdrant/payload.schema.json"], [E + "test_qdrant_browser.py", A + "QdrantBrowser.test.tsx"])
feature("F-transform", "Query transforms", ["R-015"], ["contracts/artifacts/transform.schema.json"], [E + "test_transform.py", A + "TransformView.test.tsx"])
feature("F-retrieve", "Dense / sparse / hybrid retrieval with filters", ["R-016"], ["contracts/artifacts/retrieve.schema.json"], [E + "test_retrieve.py", A + "RetrieveView.test.tsx"])
feature("F-rerank", "Reranking", ["R-017"], ["contracts/artifacts/rerank.schema.json"], [E + "test_rerank.py", A + "RerankView.test.tsx"])
feature("F-generate", "Answer generation with citations", ["R-018"], ["contracts/artifacts/generate.schema.json", "contracts/events/generate.token.schema.json"], [E + "test_generate.py", A + "GenerateView.test.tsx"])
feature("F-pipeline-graph", "Haystack pipeline graph view", ["R-019"], ["contracts/shared/pipeline-graph.schema.json"], [E + "test_pipeline_graphs.py", A + "Pipelines.test.tsx"])
feature("F-settings", "Model provider settings", ["R-020"], ["contracts/openapi/api.yaml"], [E + "test_settings.py", A + "Settings.test.tsx"])

a = lambda *n: [f"T-api-{x:03d}" for x in n]
w = lambda *n: [f"T-worker-{x:03d}" for x in n]
CORE = a(1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 19, 26) + w(5, 6, 7, 8, 9, 12)
INGEST = w(17, 22, 25, 27)
BROWSER = a(6, 7, 21)
E2E_DEPS = {
    "test_upload.py": a(1, 3, 8, 9, 10, 26),
    "test_collections.py": a(11, 26),
    "test_bootstrap.py": a(23),
    "test_status.py": a(3, 23, 24, 26) + w(10),
    "test_stage_flow.py": CORE + INGEST,
    "test_events.py": CORE + a(20) + w(17),
    "test_parse.py": CORE + w(17),
    "test_chunk.py": CORE + w(17, 22),
    "test_embed.py": CORE + w(17, 22, 25),
    "test_store.py": CORE + INGEST + BROWSER,
    "test_tags.py": CORE + INGEST + BROWSER,
    "test_qdrant_browser.py": CORE + INGEST + BROWSER,
    "test_transform.py": CORE + INGEST + a(17) + w(29),
    "test_retrieve.py": CORE + INGEST + a(17) + w(33),
    "test_rerank.py": CORE + INGEST + a(17) + w(33, 35),
    "test_generate.py": CORE + INGEST + a(17) + w(29, 33, 35, 38),
    "test_pipeline_graphs.py": a(25, 26) + w(39),
    "test_settings.py": a(12, 22, 26),
}
for t in TASKS.values():
    for p in t.get("locked", []):
        if p.startswith("tests/e2e/"):
            for d in E2E_DEPS[p.split("/")[-1]]:
                if d != t["id"] and d not in t["depends_on"]:
                    t["depends_on"].append(d)
finalize()
