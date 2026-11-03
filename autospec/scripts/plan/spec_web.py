from core import unit, ts_ctx

S = "services/web/src/"
T = "services/web/tests/"
def u(num, feat, title, src, test, cases, **kw):
    srcs = [src] if isinstance(src, str) else src
    ctx = kw.pop("ctx", None) or "\n\n".join(ts_ctx(S + s) for s in srcs)
    intro = kw.pop("intro", "")
    if intro:
        ctx = intro + "\n\n" + ctx
    return unit("web", num, feat, title, [S + s for s in srcs], T + test, ctx, cases, **kw)

A = "services/web/tests/acceptance/"
E = "tests/e2e/"
API = "Implement with `apiFetch` from src/api/client.ts (it prefixes /api/v1, sends JSON, throws ApiError). Paths and bodies: contracts/openapi/api.yaml."

u(1, "F-upload", "api wrappers batches.ts + files.ts", ["api/batches.ts", "api/files.ts"], "api/batchesFiles.test.ts", [
  "uploadBatch([fileA, fileB], 'n', ['x', 'y']) → POST /api/v1/batches multipart: formData.getAll('files') has 2 entries, name 'n', tags 'x,y'; resolves the 201 body",
  "uploadBatch(files, null, []) sends no 'name' and no 'tags' fields",
  "listBatches(10, 20) → GET /api/v1/batches?limit=10&offset=20",
  "updateBatch(id, { tags: ['a'] }) → PATCH body exactly { tags: ['a'] }",
  "ingestBatch(id, collectionId, INGEST_DEFAULTS) → POST /batches/{id}/ingest body { collection_id, params }",
  "listFiles({ batch_id: 'b', tag: undefined }) → query has batch_id=b and no tag param",
  "updateFileTags(id, ['t']) → PATCH /files/{id} { tags: ['t'] }; deleteFile resolves undefined on 204",
  "a 415 error body → promise rejects with ApiError code UNSUPPORTED_FILE_TYPE and status 415",
], intro=API)
u(2, "F-stage-flow", "api wrappers runs.ts", "api/runs.ts", "api/runs.test.ts", [
  "createIngestRun(f, c) → POST /api/v1/ingest-runs { file_id: f, collection_id: c }",
  "startIngestStage(r, 'chunk', p) → POST /api/v1/ingest-runs/r/stages/chunk { params: p }",
  "runAllIngest(r, null, params) → POST /ingest-runs/r/run-all { from_stage: null, params }",
  "createQueryRun(c, 'q?') → POST /query-runs { collection_id: c, question: 'q?' }; startQueryStage(r, 'retrieve', p) → /query-runs/r/stages/retrieve",
  "runAllQuery(r, null, params) → POST /query-runs/r/run-all { from_stage: null, params }",
  "listStageRuns(r, 'parse') → GET /stage-runs?run_id=r&stage=parse",
  "getArtifact(id) → GET /stage-runs/{id}/artifact returns the JSON; pageImageUrl('s', 2) == '/api/v1/stage-runs/s/pages/2'",
  "409 STAGE_PREREQUISITE_MISSING → ApiError with details.missing",
], intro=API)
u(3, "F-qdrant-browser", "api wrappers qdrant.ts", "api/qdrant.ts", "api/qdrant.test.ts", [
  "getQdrantInfo(c) → GET /api/v1/collections/c/qdrant",
  "scrollPoints(c, req) → POST /collections/c/qdrant/scroll with req as body",
  "countPoints(c, f) → POST /collections/c/qdrant/count { filter: f } and resolves to the number",
  "getFacet(c, 'tags') → GET /collections/c/qdrant/facets/tags",
  "getPoint(c, 'abc') → GET /collections/c/qdrant/points/abc; 404 → ApiError POINT_NOT_FOUND",
], intro=API)
u(4, "F-collections", "api wrappers settings.ts + system.ts + collections create/delete", ["api/settings.ts", "api/system.ts", "api/collections.ts"], "api/settingsSystem.test.ts", [
  "getSettings → GET /api/v1/settings; putSettings(body) → PUT with the body",
  "testConnection('ollama') → POST /settings/test-connection { target: 'ollama' } (no override key); with override → { target, override }",
  "getModels → GET /models; getStatus → GET /status",
  "listPipelineGraphs → GET /pipeline-graphs and resolves to the items array; getPipelineGraph('chunk', 'fixed') → /pipeline-graphs/chunk/fixed",
  "createCollection(body) → POST /collections; deleteCollection(id) → DELETE /collections/{id} resolves undefined",
], intro=API)
u(5, "F-live-progress", "useRunEvents hook", "hooks/useRunEvents.ts", "hooks/useRunEvents.test.ts", [
  "renderHook(() => useRunEvents('r1', fn)) → one MockEventSource with url '/api/v1/events?run_id=r1'",
  "emit('stage.progress', {...}) → fn called once with the parsed object",
  "each of the 6 types (stage.started, stage.progress, stage.completed, stage.failed, generate.token, run.updated) is delivered",
  "malformed JSON data is ignored (fn not called, no throw)",
  "unmount → source.closed true; runId null → no EventSource created",
  "rerender with another runId closes the old source and opens a new one",
], intro="Use renderHook from @testing-library/react. EventSource is globally replaced by MockEventSource (tests/setup/eventsource.ts).")
u(6, "F-live-progress", "useIngestRun + useQueryRun live hooks", "hooks/useRun.ts", "hooks/useRun.test.tsx", [
  "useIngestRun(RUN_ID) fetches GET /api/v1/ingest-runs/RUN_ID and exposes run",
  "stage.completed event → the run is refetched (msw handler called twice)",
  "stage.progress {stage_run_id 's', done 1, total 3, message 'm'} → progress['s'] == { done: 1, total: 3, message: 'm' }",
  "useQueryRun: generate.token index 0 'Hel', index 1 'lo' → tokens[stage_run_id] == 'Hello'; tokens arriving out of order (1 then 0) still join in index order",
  "run.updated → refetch",
], intro="renderHook wrapped in a QueryClientProvider (create the wrapper in the test).", deps=["T-web-002", "T-web-005"], tdeps=["T-web-002"], e2e=[E + "test_events.py"])
u(7, "F-stage-flow", "useArtifact hook", "hooks/useArtifact.ts", "hooks/useArtifact.test.tsx", [
  "useArtifact('s1') fetches /api/v1/stage-runs/s1/artifact and returns data",
  "useArtifact(null) makes no request and isLoading false",
  "404 ARTIFACT_NOT_FOUND → error is ApiError",
], deps=["T-web-002"], tdeps=["T-web-002"])
u(8, "F-upload", "TagEditor", "components/TagEditor.tsx", "components/TagEditor.test.tsx", [
  "renders chips for ['a', 'b'] with remove buttons 'remove a', 'remove b'; clicking 'remove a' → onChange(['b'])",
  "type 'Finance' + Enter → onChange(['a', 'b', 'finance'])",
  "type 'x,' (comma) → onChange with 'x' appended",
  "type 'bad tag!' + Enter → shows 'invalid tag', onChange not called",
  "duplicate 'a' → not added; 65-char tag → 'invalid tag'",
  "32 tags → input disabled",
])
u(9, "F-stage-flow", "ProgressBar", "components/ProgressBar.tsx", "components/ProgressBar.test.tsx", [
  "done 1 total 4 → role progressbar aria-valuenow 1 aria-valuemax 4, text '1/4', inner width style '25%'",
  "total 0 → width '0%'",
  "done 9 total 4 → width '100%'",
  "message shown when given",
])
u(10, "F-stage-flow", "StageStepper", "components/StageStepper.tsx", "components/StageStepper.test.tsx", [
  "4 stages, parse done v2, chunk stale v1, embed null, store failed → badges 'done v2', 'stale v1', 'not run', 'failed v1'",
  "selected 'chunk' → that button has aria-current 'step'",
  "click 'embed' → onSelect('embed')",
  "running status badge has class animate-pulse",
], intro="Build StageRun values with stageRun() from tests/setup/fixtures.ts.")
u(11, "F-stage-flow", "VersionPicker", "components/VersionPicker.tsx", "components/VersionPicker.test.tsx", [
  "GET /api/v1/stage-runs?run_id=…&stage=parse returns v2, v1 → select 'Version' with options 'v2 · done', 'v1 · failed' in that order",
  "choosing 'v1 · failed' → onSelect(v1 id)",
  "only one version → nothing rendered (no 'Version' select)",
], deps=["T-web-002"], tdeps=["T-web-002"])
u(12, "F-stage-flow", "ParamsForm", "components/ParamsForm.tsx", "components/ParamsForm.test.tsx", [
  "stage chunk with CHUNK_DEFAULTS.recursive → 'Strategy' select value 'recursive', number inputs 'length' 1000 and 'overlap' 100, text input 'separators'",
  "change Strategy to 'semantic' → onChange(CHUNK_DEFAULTS.semantic)",
  "type in 'length' → onChange with length as a number",
  "stage parse docling_layout → checkboxes 'extract_tables' and 'page_images'; toggling emits false",
  "stage embed → only a 'batch_size' number input, no Strategy select",
  "stage retrieve → 'mode' select with dense/sparse/hybrid; the filters field is not rendered",
])
u(13, "F-qdrant-browser", "FilterBuilder", "components/FilterBuilder.tsx", "components/FilterBuilder.test.tsx", [
  "click 'Add condition' → a row with key select 'tags'; nothing emitted yet",
  "facet GET /collections/c/qdrant/facets/tags → options 'finance (4)'; selecting finance → onChange({ must: [{ key: 'tags', match: { any: ['finance'] } }] })",
  "key 'page' → 'between' with two number inputs; gte 1 → onChange({ must: [{ key: 'page', range: { gte: 1 } }] })",
  "'×' removes the row → onChange({ must: [] })",
  "value prop with an existing condition renders it pre-filled",
], deps=["T-web-003"], tdeps=["T-web-003"])
u(14, "F-collections", "CreateCollectionForm", "components/CreateCollectionForm.tsx", "components/CreateCollectionForm.test.tsx", [
  "'Create' disabled while Name is empty",
  "fill name 'exp', choose dense 'all-minilm' → POST body { name: 'exp', dense_model: 'all-minilm', sparse_model: 'Qdrant/bm25' }; afterwards name input empty and onCreated called",
  "409 → alert 'COLLECTION_NAME_TAKEN: …'",
  "Dense model select has exactly the 4 models; Sparse model the 2",
], deps=["T-web-004"], tdeps=["T-web-004"], accept=[A + "Collections.test.tsx"], e2e=[E + "test_collections.py"])
u(15, "F-status", "StatusBar", "components/StatusBar.tsx", "components/StatusBar.test.tsx", [
  "while loading → 'Checking services…'",
  "8 components → 8 elements with data-ok; red one has title = detail",
  "GET /status 500 → one pill 'api' with data-ok false",
  "refetchInterval: uses react-query with refetchInterval 5000 (fake timers: advance 5 s → 2 requests)",
], deps=["T-web-004"], tdeps=["T-web-004"], accept=[A + "StatusBar.test.tsx"], e2e=[E + "test_status.py"])
u(16, "F-upload", "UploadDropzone", "components/UploadDropzone.tsx", "components/UploadDropzone.test.tsx", [
  "choose 2 files via 'Choose files' → both names listed; button 'Upload 2 files' enabled; with 0 files button disabled",
  "batch name + tag 'hr' → POST multipart has name and tags 'hr'; onUploaded(batch id); selection cleared",
  "415 response → alert with 'UNSUPPORTED_FILE_TYPE', file names still listed",
], deps=["T-web-001", "T-web-008"], tdeps=["T-web-001", "T-web-008"])
# viz
u(17, "F-parse", "PageWithBoxes", "viz/PageWithBoxes.tsx", "viz/PageWithBoxes.test.tsx", [
  "PARSE page 1 elements (5 with bbox) → 5 [data-testid=bbox]; first box style left '11.764…%' (72/612*100) top ≈ 7.58% (60/792)",
  "box border color == ELEMENT_COLORS[type]",
  "click a box → onSelect(its id); selectedId box has a thicker border (border-width differs)",
  "imageUrl null → 'No page image' and boxes still rendered",
  "legend lists 'heading' and 'text'",
])
u(18, "F-chunk", "ChunkHighlighter", "viz/ChunkHighlighter.tsx", "viz/ChunkHighlighter.test.tsx", [
  "CHUNK fixture (chunk 0 and 1 overlap) → some span has data-overlap 'true' and data-chunks '0,1'",
  "spans concatenated text == sourceText",
  "click a span covering chunks '1,2' → onSelect(1)",
  "chunk with char_start null → listed under 'Chunks without a source position'",
])
u(19, "F-chunk", "LengthHistogram", "viz/LengthHistogram.tsx", "viz/LengthHistogram.test.tsx", [
  "edges [0, 10, 20] counts [2, 3] → plot data[0].x [5, 15], y [2, 3], type 'bar'; layout.title text contains 'Chunk length'",
  "counts [] → 'No chunks', no plot",
  "bin widths passed as data[0].width [10, 10]",
])
u(20, "F-embed", "TokenView", "viz/TokenView.tsx", "viz/TokenView.test.tsx", [
  "tokens ['[CLS]', 'hi', '[SEP]'] tokenCount 3 max 256 → 3 [data-testid=token], header '3 / 256 tokens'",
  "overLimit → 'over limit — truncated by the model'",
  "tokens.length 2 < tokenCount 5000 → 'showing first 2'",
])
u(21, "F-embed", "VectorHeatmap", "viz/VectorHeatmap.tsx", "viz/VectorHeatmap.test.tsx", [
  "2 vectors of 3 dims → plot data[0].type 'heatmap', z equals vectors, y labels, colorscale 'RdBu', zmid 0",
  "title contains '2 × 3'",
  "empty → 'No vectors'",
])
u(22, "F-embed", "ScatterPlot", "viz/ScatterPlot.tsx", "viz/ScatterPlot.test.tsx", [
  "points2d for 4 points, groups ['a','a','b','b'] → 2 traces type 'scatter' named a and b",
  "click '3D' → traces type 'scatter3d'",
  "method umap and points2d null → 'Not enough chunks for UMAP 2D'",
  "hover text equals labels",
])
u(23, "F-embed", "SimilarityMatrix", "viz/SimilarityMatrix.tsx", "viz/SimilarityMatrix.test.tsx", [
  "EMBED.similarity 4x4 → heatmap z == matrix, zmin -1, zmax 1",
  "top pairs: 6 off-diagonal pairs for 4 labels, shows 5 lines with '↔', first is the max similarity (3 decimals)",
  "empty matrix → 'No vectors'",
])
u(24, "F-retrieve", "HybridLists", "viz/HybridLists.tsx", "viz/HybridLists.test.tsx", [
  "RETRIEVE → columns 'Dense', 'Sparse', 'Fused (RRF)'; fused first row shows 'D#1 S#2'",
  "dense null → no 'Dense' column",
  "click a dense row → every row with the same doc_id has data-highlighted 'true'",
  "per_query length 2 → a query selector; switching shows the second query's lists",
])
u(25, "F-rerank", "RerankDiff", "viz/RerankDiff.tsx", "viz/RerankDiff.test.tsx", [
  "RERANK → after row 1 shows '↑1' (previous 2 → 1), row 2 '↓1', row 3 '↑1'",
  "rerank_score 0.97 shown as '0.9700'; null → '—'",
  "enabled false → 'Reranking disabled — showing retrieval order'",
])
u(26, "F-generate", "TokenBudgetBar", "viz/TokenBudgetBar.tsx", "viz/TokenBudgetBar.test.tsx", [
  "GENERATE.budget → text '143 / 4000 tokens (approx.) · 2 chunks included, 1 dropped'",
  "segment widths: seg-system 1.5%, seg-question 0.2%, seg-context 1.875%",
  "used > max → widths capped so the sum is 100%",
])
u(27, "F-generate", "AnswerWithCitations", "viz/AnswerWithCitations.tsx", "viz/AnswerWithCitations.test.tsx", [
  "answer 'x [2] y [1, 2]' with 2 context items → buttons '[2]', '[1]', '[2]'",
  "click '[1]' → aria-pressed true and the chunk card with its filename shown",
  "unknown '[7]' stays plain text",
  "streaming → an element with class animate-pulse after the text",
  "context list numbered [1] and [2]",
])
u(28, "F-pipeline-graph", "PipelineGraph", "viz/PipelineGraph.tsx", "viz/PipelineGraph.test.tsx", [
  "GRAPH → node labels 'annotator' and 'splitter', class names 'ChunkAnnotator' and 'DocumentSplitter'",
  "custom node shows 'custom' badge",
  "edge label 'documents → documents'",
  "click 'splitter' → init params table with 'split_by' and '\"word\"'",
], intro="@xyflow/react renders in jsdom with the global ResizeObserver stub; give the container a fixed height style.")
# stage views
views = [("Parse", "F-parse", [17], ["2 pages · 8 elements · 0 tables", "page select switches to page 2 boxes", "selecting an element in the list highlights its box", "tables render as <table> with <th> header cells (use a modified fixture with a table element)"]),
         ("Chunk", "F-chunk", [18, 19], ["header '4 chunks · <min>–<max> chars · mean <mean>' and 'recursive'", "tabs Source / Cards / Histogram; Cards shows '#0' with section path joined by ' › '", "semantic artifact (fixture with semantic gaps) → 'Breakpoints' tab with ✂ markers"]),
         ("Embed", "F-embed", [20, 21, 22, 23], ["'4 chunks · all-minilm (384d) · Qdrant/bm25' and '1 over limit'", "Tokens tab: chunk selector switches TokenView", "Projection tab PCA uses projections.pca2; UMAP null → not-enough message", "Similarity tab renders SimilarityMatrix"]),
         ("Store", "F-store", [], ["'4 points written to rf_…'", "vector config table shows text-dense 384 Cosine and text-sparse idf", "payload sample <pre> contains 'meta'", "points_deleted > 0 → '<n> old points replaced'"]),
         ("Transform", "F-transform", [], ["queries listed under 'Search queries'", "hyde artifact → quote block with hyde_document", "strategy none → 'No transformation — the question is used as is.'", "'Prompt' collapsible shows system message"]),
         ("Retrieve", "F-retrieve", [24], ["header 'hybrid · top_k 10 · RRF k 60'", "filter chip 'tags in finance'", "renders HybridLists"]),
         ("Rerank", "F-rerank", [25], ["header 'Xenova/ms-marco-MiniLM-L-6-v2 · top 3'", "renders RerankDiff rows", "disabled artifact shows the disabled banner"]),
         ("Generate", "F-generate", [26, 27], ["TokenBudgetBar + answer with citation buttons", "liveText 'Revenue gr' replaces the answer while streaming", "footer 'ollama · qwen3:8b' and '210 prompt / 18 completion tokens'"])]
n = 29
VIEW_IDS = {}
for name, feat, deps, cases in views:
    accept = [] if name == "Generate" else [A + f"{name}View.test.tsx"]
    e2e_map = {"Parse": "test_parse.py", "Chunk": "test_chunk.py", "Embed": "test_embed.py", "Store": "test_store.py", "Transform": "test_transform.py", "Retrieve": "test_retrieve.py", "Rerank": "test_rerank.py"}
    e2e = [E + e2e_map[name]] if name in e2e_map else []
    if name == "Store":
        e2e.append(E + "test_tags.py")
    VIEW_IDS[name] = u(n, feat, f"{name}View", f"components/stages/{name}View.tsx", f"stages/{name}View.test.tsx", cases,
                       deps=[f"T-web-{d:03d}" for d in deps], tdeps=[f"T-web-{d:03d}" for d in deps], accept=accept, e2e=e2e,
                       intro="Fixtures from tests/setup/fixtures.ts; derive variants with spread, e.g. { ...CHUNK, strategy: 'semantic', semantic: {...} }.")
    n += 1
u(37, "F-stage-flow", "StagePanel", "components/StagePanel.tsx", "components/StagePanel.test.tsx", [
  "run null (stage chunk) → ParamsForm with CHUNK_DEFAULTS.recursive, button 'Run chunk' → POST /ingest-runs/r/stages/chunk { params }",
  "409 response → alert 'STAGE_PREREQUISITE_MISSING: …'",
  "run running + progress {1, 2, 'm'} → progressbar",
  "run failed with error {code PARSE_FAILED} → 'PARSE_FAILED: …'",
  "run stale → 'Outdated — an earlier stage was re-run'",
  "run done → artifact fetched and the stage view rendered (vi.mock the view module to a stub that prints 'VIEW <stageRunId>')",
  "stage retrieve → FilterBuilder rendered (vi.mock FilterBuilder)",
], deps=["T-web-007", "T-web-009", "T-web-011", "T-web-012"], tdeps=["T-web-002"])
u(38, "F-upload", "FilesPage", "pages/FilesPage.tsx", "pages/FilesPage.test.tsx", [
  "batches listed with file rows: filename, type, size '470.8 KB' for 482113 bytes",
  "'Ingest…' on a file → collection select + 'Start' → POST /ingest-runs then navigates to /ingest/<id> (assert via a route element in renderWithProviders)",
  "'Delete' with window.confirm mocked true → DELETE /files/{id}",
  "'Ingest batch' → POST /batches/{id}/ingest with INGEST_DEFAULTS and shows '<n> runs started'",
], deps=["T-web-001", "T-web-002", "T-web-008", "T-web-016"], tdeps=["T-web-001"], accept=[A + "Upload.test.tsx"], e2e=[E + "test_upload.py"])
u(39, "F-stage-flow", "IngestRunPage", "pages/IngestRunPage.tsx", "pages/IngestRunPage.test.tsx", [
  "header shows filename and 'Run all'; stepper with 4 stages; default selection = first stage not done",
  "'Run all' → POST /ingest-runs/r/run-all { from_stage: null, params } where params uses each stage's current params or INGEST_DEFAULTS",
  "pending plan chips for run_all_pending ['embed', 'store']",
  "selecting 'embed' shows its StagePanel (vi.mock StagePanel to print the stage)",
], deps=["T-web-006", "T-web-010", "T-web-037", VIEW_IDS["Parse"]], tdeps=["T-web-002"], accept=[A + "IngestRun.test.tsx"], e2e=[E + "test_stage_flow.py"])
u(40, "F-qdrant-browser", "QdrantBrowserPage", "pages/QdrantBrowserPage.tsx", "pages/QdrantBrowserPage.test.tsx", [
  "info card: status 'green', '4 points', payload index table rows",
  "points table first row: id first 8 chars, filename, page, element_type",
  "'Load more' appears when next_offset is set and sends it as offset",
  "row click → side panel with first 16 dims and '… (368 more)'",
  "collection select change navigates to /qdrant/<id>",
], deps=["T-web-003", "T-web-013"], tdeps=["T-web-003"], accept=[A + "QdrantBrowser.test.tsx"], e2e=[E + "test_qdrant_browser.py"])
u(41, "F-settings", "SettingsPage", "pages/SettingsPage.tsx", "pages/SettingsPage.test.tsx", [
  "loads settings: radio 'ollama' checked, Ollama URL input value, Anthropic key placeholder 'sk-…abcd'",
  "'Remove key' checked + Save → anthropic.api_key ''",
  "new key typed → api_key '<key>'; untouched → null",
  "'Test connection' for OpenAI-compatible sends override { base_url, api_key }; failure → '✗ <detail>'",
  "dense table shows 'ollama pull all-minilm' for not installed models",
  "422 on save → alert with VALIDATION_ERROR",
], deps=["T-web-004"], tdeps=["T-web-004"], accept=[A + "Settings.test.tsx"], e2e=[E + "test_settings.py"])
u(42, "F-pipeline-graph", "PipelinesPage", "pages/PipelinesPage.tsx", "pages/PipelinesPage.test.tsx", [
  "graphs grouped as 'chunk / fixed' entries; first graph selected by default",
  "clicking another entry renders its PipelineGraph (vi.mock PipelineGraph to print variant)",
  "empty → 'No pipeline graphs reported yet — is the worker running?'",
], deps=["T-web-004", "T-web-028"], tdeps=["T-web-004"], accept=[A + "Pipelines.test.tsx"], e2e=[E + "test_pipeline_graphs.py"])
u(43, "F-generate", "QueryPage", "pages/QueryPage.tsx", "pages/QueryPage.test.tsx", [
  "/query: collection select + question + 'Ask' → POST /query-runs then navigates to /query/<id>",
  "'Ask' disabled for an empty question",
  "/query/:runId → question header, stepper transform/retrieve/rerank/generate, 'Run all' → POST /query-runs/<id>/run-all { from_stage: null, params } with TRANSFORM/RETRIEVE/RERANK/GENERATE defaults",
  "generate panel receives liveText from generate.token events (vi.mock StagePanel to print liveText)",
], deps=["T-web-006", "T-web-010", "T-web-037"] + [VIEW_IDS[v] for v in ("Transform", "Retrieve", "Rerank", "Generate")], tdeps=["T-web-002"],
   accept=[A + "GenerateView.test.tsx"], e2e=[E + "test_generate.py"])
