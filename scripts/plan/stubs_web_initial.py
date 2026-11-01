import os, textwrap
T = "../api/types"
# (path, imports-from-types, body)
F = {}
def comp(path, name, props, doc, types=(), extra_imports=""):
    imp = f"import type {{ {', '.join(sorted(set(types)))} }} from '{T if path.count('/')==1 else '../'+T}'\n" if types else ""
    F[path] = f"""{extra_imports}{imp}
export interface {name}Props {{
{textwrap.indent(props.strip(), '  ')}
}}

/**
{textwrap.indent(textwrap.dedent(doc).strip(), ' * ', lambda l: True)}
 */
export function {name}(_props: {name}Props): React.ReactElement {{
  throw new Error('not implemented')
}}
"""
def mod(path, body): F[path]=body

# ---------------- api wrappers
mod("api/batches.ts", """import type { BatchList, BatchWithFiles, Batch, IngestParamsAll, IngestRun } from './types'

/** POST /batches multipart: one 'files' part per file, 'name' only when given, 'tags' = tags.join(',')
 * only when tags non-empty. → 201 BatchWithFiles. */
export function uploadBatch(_files: File[], _name: string | null, _tags: string[]): Promise<BatchWithFiles> {
  throw new Error('not implemented')
}

/** GET /batches?limit=&offset= */
export function listBatches(_limit = 50, _offset = 0): Promise<BatchList> {
  throw new Error('not implemented')
}

export function getBatch(_id: string): Promise<BatchWithFiles> {
  throw new Error('not implemented')
}

/** PATCH /batches/{id} with only the given fields. */
export function updateBatch(_id: string, _patch: { name?: string; tags?: string[] }): Promise<Batch> {
  throw new Error('not implemented')
}

/** POST /batches/{id}/ingest → 202 { items: IngestRun[] }. */
export function ingestBatch(
  _id: string,
  _collectionId: string,
  _params: IngestParamsAll,
): Promise<{ items: IngestRun[] }> {
  throw new Error('not implemented')
}
""")
mod("api/files.ts", """import type { FileItem, FileList } from './types'
import { API_BASE } from './client'

/** GET /files with optional filters; omitted/undefined filters are not sent. */
export function listFiles(_q: {
  limit?: number
  offset?: number
  batch_id?: string
  tag?: string
  mime?: string
}): Promise<FileList> {
  throw new Error('not implemented')
}

export function getFile(_id: string): Promise<FileItem> {
  throw new Error('not implemented')
}

/** PATCH /files/{id} { tags }. */
export function updateFileTags(_id: string, _tags: string[]): Promise<FileItem> {
  throw new Error('not implemented')
}

export function deleteFile(_id: string): Promise<void> {
  throw new Error('not implemented')
}

export function fileContentUrl(id: string): string {
  return `${API_BASE}/files/${id}/content`
}
""")
mod("api/runs.ts", """import type {
  IngestParamsAll,
  IngestRun,
  IngestStage,
  QueryRun,
  QueryStage,
  Stage,
  StageRun,
  StageRunList,
} from './types'
import { API_BASE } from './client'

/** POST /ingest-runs → 201 IngestRun. */
export function createIngestRun(_fileId: string, _collectionId: string): Promise<IngestRun> {
  throw new Error('not implemented')
}

export function getIngestRun(_runId: string): Promise<IngestRun> {
  throw new Error('not implemented')
}

/** POST /ingest-runs/{runId}/stages/{stage} { params } → 202 StageRun. */
export function startIngestStage(_runId: string, _stage: IngestStage, _params: object): Promise<StageRun> {
  throw new Error('not implemented')
}

/** POST /ingest-runs/{runId}/run-all { from_stage, params } → IngestRun (200 or 202). */
export function runAllIngest(
  _runId: string,
  _fromStage: IngestStage | null,
  _params: IngestParamsAll,
): Promise<IngestRun> {
  throw new Error('not implemented')
}

/** POST /query-runs → 201 QueryRun. */
export function createQueryRun(_collectionId: string, _question: string): Promise<QueryRun> {
  throw new Error('not implemented')
}

export function getQueryRun(_runId: string): Promise<QueryRun> {
  throw new Error('not implemented')
}

/** POST /query-runs/{runId}/stages/{stage} { params } → 202 StageRun. */
export function startQueryStage(_runId: string, _stage: QueryStage, _params: object): Promise<StageRun> {
  throw new Error('not implemented')
}

/** GET /stage-runs?run_id=&stage= (all versions, newest first). */
export function listStageRuns(_runId: string, _stage: Stage): Promise<StageRunList> {
  throw new Error('not implemented')
}

/** GET /stage-runs/{id}/artifact. */
export function getArtifact<T>(_stageRunId: string): Promise<T> {
  throw new Error('not implemented')
}

export function pageImageUrl(stageRunId: string, pageNo: number): string {
  return `${API_BASE}/stage-runs/${stageRunId}/pages/${pageNo}`
}
""")
mod("api/qdrant.ts", """import type { FacetResponse, PayloadFilter, QdrantInfo, QdrantPoint, ScrollResponse } from './types'

export function getQdrantInfo(_collectionId: string): Promise<QdrantInfo> {
  throw new Error('not implemented')
}

/** POST /collections/{id}/qdrant/scroll. */
export function scrollPoints(
  _collectionId: string,
  _req: { filter: PayloadFilter; limit: number; offset: string | null; with_vectors: boolean },
): Promise<ScrollResponse> {
  throw new Error('not implemented')
}

/** POST /collections/{id}/qdrant/count → number. */
export function countPoints(_collectionId: string, _filter: PayloadFilter): Promise<number> {
  throw new Error('not implemented')
}

export function getFacet(_collectionId: string, _key: string): Promise<FacetResponse> {
  throw new Error('not implemented')
}

export function getPoint(_collectionId: string, _pointId: string): Promise<QdrantPoint> {
  throw new Error('not implemented')
}
""")
mod("api/settings.ts", """import type { ModelCatalog, Settings, SettingsUpdate, TestConnectionResult } from './types'

export function getSettings(): Promise<Settings> {
  throw new Error('not implemented')
}

export function putSettings(_body: SettingsUpdate): Promise<Settings> {
  throw new Error('not implemented')
}

/** POST /settings/test-connection { target, override? }. */
export function testConnection(
  _target: 'ollama' | 'anthropic' | 'openai_compatible',
  _override?: { base_url: string | null; api_key: string | null },
): Promise<TestConnectionResult> {
  throw new Error('not implemented')
}

export function getModels(): Promise<ModelCatalog> {
  throw new Error('not implemented')
}
""")
mod("api/system.ts", """import type { PipelineGraph, Status } from './types'

export function getStatus(): Promise<Status> {
  throw new Error('not implemented')
}

/** GET /pipeline-graphs → items. */
export function listPipelineGraphs(): Promise<PipelineGraph[]> {
  throw new Error('not implemented')
}

export function getPipelineGraph(_stage: string, _variant: string): Promise<PipelineGraph> {
  throw new Error('not implemented')
}
""")
# ---------------- hooks
mod("hooks/useRunEvents.ts", """import type { RunEvent } from '../api/types'

/** Opens EventSource(`${API_BASE}/events?run_id=${runId}`) while runId is non-null; for each of the
 * 6 event types (addEventListener per type) parses event.data as JSON and calls onEvent.
 * Closes on unmount or runId change. Malformed JSON is ignored. */
export function useRunEvents(_runId: string | null, _onEvent: (e: RunEvent) => void): void {
  throw new Error('not implemented')
}
""")
mod("hooks/useRun.ts", """import type { IngestRun, QueryRun } from '../api/types'

export interface LiveRun<T> {
  run: T | undefined
  error: unknown
  /** latest stage.progress per stage_run_id */
  progress: Record<string, { done: number; total: number; message: string }>
  /** generate.token texts joined in index order per stage_run_id */
  tokens: Record<string, string>
}

/** react-query ['ingest-run', runId] via getIngestRun + useRunEvents: run.updated, stage.started,
 * stage.completed, stage.failed → invalidate the query; stage.progress → progress map. */
export function useIngestRun(_runId: string): LiveRun<IngestRun> {
  throw new Error('not implemented')
}

/** Same for query runs (['query-run', runId], getQueryRun); generate.token → tokens map. */
export function useQueryRun(_runId: string): LiveRun<QueryRun> {
  throw new Error('not implemented')
}
""")
mod("hooks/useArtifact.ts", """/** react-query ['artifact', stageRunId] via getArtifact<T>; disabled when stageRunId is null;
 * staleTime Infinity (artifacts never change). */
export function useArtifact<T>(_stageRunId: string | null): { data: T | undefined; error: unknown; isLoading: boolean } {
  throw new Error('not implemented')
}
""")
# ---------------- components
comp("components/CreateCollectionForm.tsx","CreateCollectionForm","onCreated?: () => void","""
Inline form: name input (label "Name"), dense model select (label "Dense model", 4 options from
DenseModel), sparse model select (label "Sparse model"), button "Create". Submit → createCollection;
success → invalidate ['collections'], clear name, onCreated(); ApiError → <ErrorBox>. Button disabled
while name is empty or the request is pending.""")
comp("components/StatusBar.tsx","StatusBar","","""
Polls getStatus every 5 s (react-query refetchInterval). Renders one pill per component in response
order: text = component name, data-ok="true|false", green when ok, red when not with title = detail.
While loading: "Checking services…". Request error: one red pill "api" with the error message.""")
comp("components/UploadDropzone.tsx","UploadDropzone","onUploaded: (batchId: string) => void","""
Drop zone + hidden <input type="file" multiple aria-label="Choose files">. Selected files listed by
name. Optional batch name input (label "Batch name") and <TagEditor> for batch tags. Button
"Upload N files" (disabled with 0 files) → uploadBatch → onUploaded(batch.id), clear selection.
ApiError (e.g. UNSUPPORTED_FILE_TYPE) → <ErrorBox>, selection kept.""", extra_imports="")
comp("components/TagEditor.tsx","TagEditor","tags: string[]\nonChange: (tags: string[]) => void","""
Chips for each tag with a "×" button (aria-label "remove <tag>"). Text input (aria-label "Add tag"):
Enter or ',' adds the trimmed lowercased value if it matches /^[a-z0-9][a-z0-9_.:-]*$/, is ≤64 chars and
not a duplicate; otherwise shows "invalid tag" and does not call onChange. Max 32 tags (input disabled).""")
comp("components/StageStepper.tsx","StageStepper","stages: { name: string; run: StageRun | null }[]\nselected: string\nonSelect: (stage: string) => void","""
Horizontal steps in the given order. Each step is a button with the stage name and a status badge:
"not run" when run is null, else run.status (+ " v<version>"). Badge colors: done green, failed red,
running/queued blue (with animate-pulse), stale amber. aria-current="step" on the selected one.""", types=["StageRun"])
comp("components/ProgressBar.tsx","ProgressBar","done: number\ntotal: number\nmessage?: string","""
role="progressbar" with aria-valuenow=done, aria-valuemax=total, width % = round(done/total*100)
(0 when total ≤ 0, max 100). Shows "<done>/<total>" and message when given.""")
comp("components/VersionPicker.tsx","VersionPicker","runId: string\nstage: Stage\nselectedId: string | null\nonSelect: (stageRunId: string) => void","""
<select aria-label="Version"> listing listStageRuns(runId, stage) items as "v<version> · <status>",
newest first; value = selectedId; change → onSelect(id). Hidden when there are < 2 versions.""", types=["Stage"])
comp("components/FilterBuilder.tsx","FilterBuilder","collectionId: string\nvalue: PayloadFilter\nonChange: (f: PayloadFilter) => void","""
Edits value.must only. Rows: key select (file_id, batch_id, tags, mime, element_type, chunk_strategy,
parse_strategy, page, chunk_index) + operator: keyword keys → "is any of" with a multi-select whose
options come from getFacet(collectionId, key) ("value (count)"); page/chunk_index → "between" with two
number inputs (gte/lte, empty = omitted). "Add condition" button appends {key: 'tags', match: {any: []}}
(not emitted until it has ≥1 value); "×" removes a row. Emits only complete conditions.""", types=["PayloadFilter"])
comp("components/ParamsForm.tsx","ParamsForm","stage: Stage\nvalue: Record<string, unknown>\nonChange: (v: Record<string, unknown>) => void","""
Generic params editor for every stage (except retrieve filters, handled by FilterBuilder).
parse/chunk/transform: first a "Strategy" select (parse: docling_layout|docling_ocr|plain_text, chunk:
fixed|sentence|recursive|semantic|structure|table, transform: none|rewrite|multi_query|hyde); changing
it resets value to lib/defaults for that strategy. Then one labelled input per remaining field of the
current value: number → <input type="number"> (label = field name), boolean → checkbox, string enum
(split_by, mode) → select, string[] (separators) → comma-separated text input showing "\\n" for
newlines. Emits a new object on every change (numbers parsed with Number()).""", types=["Stage"])
# ---------------- viz
comp("viz/PageWithBoxes.tsx","PageWithBoxes","imageUrl: string | null\nwidth: number\nheight: number\nelements: ParseArtifact['elements']\nselectedId?: string | null\nonSelect?: (elementId: string) => void","""
Page image (<img alt="page">) in a relative container; for every element with a bbox an absolutely
positioned <div data-testid="bbox" data-element-id=…> at left/top/width/height in % of the page
(l/width*100, t/height*100, (r-l)/width*100, (b-t)/height*100), border color ELEMENT_COLORS[type],
title = "<type>: <first 80 chars of text>". Click → onSelect(id). selectedId gets a thicker border.
imageUrl null → grey placeholder "No page image" with the boxes still drawn on a width:height box.
Legend below: one entry per element type present.""", types=["ParseArtifact"])
comp("viz/ChunkHighlighter.tsx","ChunkHighlighter","sourceText: string\nchunks: ChunkArtifact['chunks']\nselectedIndex?: number | null\nonSelect?: (index: number) => void","""
Renders sourceText as segments split at every chunk char_start/char_end boundary. Each segment's
background = CHUNK_COLORS[first covering chunk index % 10]; a segment covered by ≥2 chunks (overlap)
gets data-overlap="true" and a striped/darker style; uncovered segments plain. Each segment
<span data-chunks="0,1"> lists covering indices. Click → onSelect(lowest covering index). Chunks with
char_start null are listed below as "Chunks without a source position" cards.""", types=["ChunkArtifact"])
comp("viz/LengthHistogram.tsx","LengthHistogram","binEdges: number[]\ncounts: number[]","""
Plotly bar chart (react-plotly.js <Plot>): x = bin centers ((edge[i]+edge[i+1])/2), y = counts,
width = bin width, layout title "Chunk length (chars)". Empty counts → text "No chunks".""", extra_imports="")
comp("viz/TokenView.tsx","TokenView","tokens: string[]\ntokenCount: number\nmaxTokens: number\noverLimit: boolean","""
Token pills in order (alternating two background colors, data-testid="token"), header
"<tokenCount> / <maxTokens> tokens", red badge "over limit — truncated by the model" when overLimit,
note "showing first <tokens.length>" when tokens.length < tokenCount.""")
comp("viz/VectorHeatmap.tsx","VectorHeatmap","vectors: number[][]\nlabels: string[]","""
Plotly heatmap: z = vectors (rows = chunks, labels on y), x = dimension index, colorscale 'RdBu',
zmid 0, layout title "Dense vectors (<n> × <dims>)". Empty → "No vectors".""")
comp("viz/ScatterPlot.tsx","ScatterPlot","points2d: number[][] | null\npoints3d: number[][] | null\nlabels: string[]\ngroups: string[]\nmethod: 'pca' | 'umap'","""
Toggle buttons "2D" / "3D" (default 2D). 2D → Plotly 'scatter' mode markers; 3D → 'scatter3d'.
One trace per distinct group (legend), hover text = labels[i]. Selected dimension's points null →
message "Not enough chunks for <METHOD> <2D|3D>". Title "<PCA|UMAP> projection".""")
comp("viz/SimilarityMatrix.tsx","SimilarityMatrix","matrix: number[][]\nlabels: string[]","""
Plotly heatmap, z = matrix, x = y = labels, zmin -1, zmax 1, colorscale 'Viridis', title
"Cosine similarity". Below: the 5 most similar off-diagonal pairs (i<j) as "<label i> ↔ <label j>:
<value to 3 decimals>", sorted desc. Empty → "No vectors".""")
comp("viz/HybridLists.tsx","HybridLists","artifact: RetrieveArtifact","""
Three columns for per_query[0] (with a query selector when per_query.length > 1): "Dense", "Sparse"
(column omitted when the list is null), "Fused (RRF)" from artifact.fused. Each row: rank, score (4
decimals), first 120 chars, filename + page. Hovering/clicking a row highlights the same doc_id in all
columns (data-highlighted="true"). Fused rows show source ranks as "D#2 S#5".""", types=["RetrieveArtifact"])
comp("viz/RerankDiff.tsx","RerankDiff","artifact: RerankArtifact","""
Two columns "Before" (artifact.before) and "After" (artifact.after[].hit). After rows show
"↑3" (green) / "↓2" (red) / "=" from previous_rank − new rank, plus rerank_score (4 decimals) or "—".
disabled → banner "Reranking disabled — showing retrieval order".""", types=["RerankArtifact"])
comp("viz/TokenBudgetBar.tsx","TokenBudgetBar","budget: GenerateArtifact['budget']","""
Stacked horizontal bar of max_context_tokens: system (grey), question (blue), context (green), free
(white). Each segment has data-testid="seg-<name>" and width % of max. Text "<used total> /
<max_context_tokens> tokens (approx.) · <chunks_included> chunks included, <chunks_dropped>
dropped" where used total = system + question + used_context.""", types=["GenerateArtifact"])
comp("viz/AnswerWithCitations.tsx","AnswerWithCitations","answer: string\ncontext: GenerateArtifact['context']\nstreaming?: boolean","""
Answer text where every "[n]" / "[n, m]" marker becomes buttons "[n]" (one per number) that map to
context[n] (unknown n → plain text). Clicking a citation shows that chunk card (filename, page,
text) below and marks the button aria-pressed. streaming → blinking cursor after the text.
Below the answer: the context list numbered [1]..[k].""", types=["GenerateArtifact"])
comp("viz/PipelineGraph.tsx","PipelineGraph","graph: PipelineGraph","""
@xyflow/react <ReactFlow> read-only: one node per graph.nodes (label = name, sublabel = class name
after the last '.', custom nodes highlighted with a purple border and "custom" badge), one edge per
graph.edges (label "sender_socket → receiver_socket"). Layout: nodes left-to-right in topological
order (x = depth*260, y = index within depth*110). Clicking a node shows its init_params as a
name/value table beside the graph.""", types=["PipelineGraph"])
# ---------------- stage views
for st, art, doc in [
 ("Parse","ParseArtifact","""Left: page selector (pages[]) + <PageWithBoxes> using pageImageUrl(stageRunId, page). Right:
element list for the page (type badge in ELEMENT_COLORS, text); selecting an element in either place
selects it in both. Tables render as an HTML <table> from table.cells (header cells as <th>).
Header line: "<n> pages · <m> elements · <t> tables" + "OCR used" badge when ocr_used. Formats
without pages: just the element list."""),
 ("Chunk","ChunkArtifact","""Header: "<count> chunks · <min>–<max> chars · mean <mean>" + strategy name. Tabs "Source"
(<ChunkHighlighter>), "Cards" (one card per chunk: #index, element_type badge, pages, section path
joined ' › ', text), "Histogram" (<LengthHistogram>). Semantic strategy: extra tab "Breakpoints"
listing gaps with distance (3 decimals) and a ✂ marker where is_break."""),
 ("Embed","EmbedArtifact","""Header: "<n> chunks · <dense_model> (<dims>d) · <sparse_model>" + "<k> over limit" badge.
Tabs: "Tokens" (chunk selector + <TokenView>), "Heatmap" (<VectorHeatmap> of sampled chunks' dense
vectors, labels "#index"), "Projection" (method toggle PCA/UMAP + <ScatterPlot>, groups = chunk
element_type from the chunk artifact when given via props.chunks else 'chunk'), "Similarity"
(<SimilarityMatrix> labels "#index"). Notice: "Vectors are not stored yet — run Store to write them
to Qdrant." """),
 ("Store","StoreArtifact","""Summary: "<points_written> points written to <qdrant_collection>" (+ "<points_deleted> old
points replaced" when > 0). Vector config table (dense name/size/distance, sparse name/modifier).
Payload sample as pretty JSON (<pre>) with filterable keys (meta.*) highlighted. Link "Open in Qdrant
browser" → /qdrant/<collectionId>."""),
 ("Transform","TransformArtifact","""Strategy name; "Original question" box; list "Search queries" (queries[]); for hyde the
hypothetical document in a quote block; collapsible "Prompt" showing messages (role + content).
strategy none → "No transformation — the question is used as is." """),
 ("Retrieve","RetrieveArtifact","""Header "<mode> · top_k <k> · RRF k <rrf_k>" and active filters as chips ("tags in finance");
then <HybridLists>."""),
 ("Rerank","RerankArtifact","""Header "<model> · top <top_n>" (or disabled banner via RerankDiff) then <RerankDiff>."""),
 ("Generate","GenerateArtifact","""<TokenBudgetBar>, then <AnswerWithCitations answer context>; while props.liveText is set
(streaming) render that text instead with streaming=true. Collapsible "Prompt" with messages.
Footer: provider/model and usage tokens when not null."""),
]:
    extra = "\ncollectionId?: string" if st=="Store" else ("\nchunks?: ChunkArtifact['chunks']" if st=="Embed" else ("\nliveText?: string | null" if st=="Generate" else ""))
    types=[art]+(["ChunkArtifact"] if st=="Embed" else [])
    comp(f"components/stages/{st}View.tsx", f"{st}View", f"stageRunId: string\nartifact: {art}{extra}", doc, types=types)
# ---------------- panels + pages
comp("components/StagePanel.tsx","StagePanel","runId: string\nrunKind: 'ingest' | 'query'\nstage: Stage\nrun: StageRun | null\nprogress?: { done: number; total: number; message: string }\nliveText?: string | null\nextra?: Record<string, unknown>","""
One stage of a run: <ParamsForm> initialised from run.params (or lib/defaults), "Run <stage>" button
→ startIngestStage / startQueryStage (ApiError → ErrorBox, e.g. STAGE_PREREQUISITE_MISSING), status
line, <ProgressBar> while queued/running, error box when failed (error.code: error.message), stale
banner "Outdated — an earlier stage was re-run", <VersionPicker>; when the selected version is done:
useArtifact + the stage's <XView> (props from `extra`: collectionId, chunks). Retrieve stage also
shows <FilterBuilder> bound to params.filters (needs extra.collectionId).""", types=["Stage","StageRun"])
comp("pages/FilesPage.tsx","FilesPage","","""
Route "/". <UploadDropzone> on top; then batches (listBatches) each with its files table: filename,
type, size (KB/MB, 1 decimal), tags (<TagEditor> → updateFileTags), actions "Ingest…" (collection
select + "Start" → createIngestRun then navigate to /ingest/<runId>) and "Delete" (confirm →
deleteFile). Batch row: name, tags editor (updateBatch), "Ingest batch" (collection select → ingestBatch
with INGEST_DEFAULTS, then shows "<n> runs started" with links).""")
comp("pages/IngestRunPage.tsx","IngestRunPage","","""
Route "/ingest/:runId". useIngestRun(runId). Header: filename, collection, "Run all" button
(runAllIngest(runId, null, current params of each stage or INGEST_DEFAULTS)) and pending plan chips.
<StageStepper> for parse/chunk/embed/store (default selection: first stage not done, else store) and
the selected <StagePanel>. Passes extra.chunks (from the active chunk artifact) to the embed panel
and extra.collectionId to store. Loading/error states as in CollectionsPage.""")
comp("pages/QueryPage.tsx","QueryPage","","""
Route "/query" (new) and "/query/:runId". New: collection select + question textarea + "Ask" →
createQueryRun → navigate to /query/<id>. With runId: useQueryRun; header with the question and
"Run all" (runAllQuery equivalent: POST /query-runs/{id}/run-all via startQueryStage chain is NOT
used — call apiFetch run-all with from_stage null and defaults); <StageStepper> transform/retrieve/
rerank/generate + selected <StagePanel> (generate gets liveText from tokens).""")
comp("pages/QdrantBrowserPage.tsx","QdrantBrowserPage","","""
Route "/qdrant/:collectionId?". Collection select (navigates). Info card from getQdrantInfo (exists,
status, points_count, vector config, payload indexes table). <FilterBuilder> + matching count
(countPoints). Points table (scrollPoints limit 20, "Load more" with next_offset): point id (first 8),
filename, page, element_type, tags, content (80 chars). Click row → side panel with getPoint raw JSON
(<pre>) incl. the first 16 dense dims + "… (<n> more)". exists false → "Nothing stored yet in this
collection — run the Store stage of an ingest run." """)
comp("pages/SettingsPage.tsx","SettingsPage","","""
Route "/settings". Loads getSettings + getModels. Radio "Chat provider" (ollama | anthropic |
openai_compatible). Sections: Ollama (URL, chat model select from installed models or free text),
Anthropic (model, API key password input showing api_key_masked as placeholder, "Remove key"
checkbox → api_key ""), OpenAI-compatible (base URL, model, API key). Reranker model select.
"Test connection" per provider → testConnection(target, unsaved override) → "✓ <n> models, <ms> ms"
or "✗ <detail>". "Save" → putSettings (api_key null when the field was left empty). ApiError →
ErrorBox. Dense model table from getModels with installed ✓/✗ and hint `ollama pull <model>`.""")
comp("pages/PipelinesPage.tsx","PipelinesPage","","""
Route "/pipelines". listPipelineGraphs → left list grouped by stage ("chunk / semantic"), selected
graph rendered with <PipelineGraph>. Empty → "No pipeline graphs reported yet — is the worker
running?" """)

for path, body in F.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f: f.write(body.lstrip("\n"))
print(len(F))
