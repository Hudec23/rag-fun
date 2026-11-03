from core import unit, py_ctx

S = "services/worker/src/rag_worker/"
T = "services/worker/tests/"
def u(num, feat, title, src, test, names, cases, **kw):
    srcs = [src] if isinstance(src, str) else src
    ctx = kw.pop("ctx", None) or py_ctx(S + srcs[0], names, kw.pop("intro", ""))
    return unit("worker", num, feat, title, [S + s for s in srcs], T + test, ctx, cases, **kw)

QT = "Integration test against qdrant-test (QDRANT_URL); use collection 'rf_' + uuid4().hex and delete it afterwards."
u(1, "F-chunk", "chunk_stats", "viz/stats.py", "unit/test_viz_stats.py", ["chunk_stats"], [
  "chunk_stats([]) == {'count': 0, 'min_chars': 0, 'max_chars': 0, 'mean_chars': 0, 'histogram': {'bin_edges': [], 'counts': []}}",
  "chunk_stats([10]) → count 1, min = max = 10, mean 10.0, len(counts) == 1, sum(counts) == 1",
  "chunk_stats([10, 20, 30, 40]) → mean 25.0, bins == 4, len(bin_edges) == 5, bin_edges[0] == 10.0, bin_edges[-1] == 40.0",
  "25 values → exactly 20 bins; sum(counts) == 25",
  "mean rounded to 2 decimals: [1, 2, 2] → 1.67",
])
u(2, "F-embed", "sample_indices", "viz/sampling.py", "unit/test_viz_sampling.py", ["sample_indices"], [
  "sample_indices(0) == []; sample_indices(1) == [0]",
  "sample_indices(5) == [0, 1, 2, 3, 4]",
  "sample_indices(1000) has length 200, starts 0, ends 999, strictly increasing ints",
  "sample_indices(10, cap=3) == [0, 4, 9] (round(linspace(0, 9, 3)) = 0, 4.5→4 (banker's), 9) — assert len 3, first 0, last 9, unique",
])
u(3, "F-embed", "PCA + UMAP projections", "viz/projection.py", "unit/test_viz_projection.py", ["pca", "umap_project"], [
  "pca(10 random seeded vectors of dim 8, k=2) → 10 rows of 2 floats, explained variance list of 2 values in [0, 1] summing ≤ 1",
  "pca same input twice → identical output (deterministic)",
  "pca(vectors of length 1, k=2) → (None, [])",
  "pca(5 identical vectors, k=2) → all coords 0.0, explained [] (no exception)",
  "umap_project(4 vectors, 2) is None; umap_project(12 seeded vectors, 3) → 12 rows of 3 floats, deterministic",
], intro="Generate inputs with numpy.random.default_rng(0).normal(size=(n, d)).tolist().")
u(4, "F-embed", "cosine similarity matrix", "viz/similarity.py", "unit/test_viz_similarity.py", ["cosine_matrix"], [
  "cosine_matrix([]) == []",
  "[[1,0],[0,1],[1,1]] → [[1.0, 0.0, 0.707107], [0.0, 1.0, 0.707107], [0.707107, 0.707107, 1.0]]",
  "zero vector row → diagonal still 1.0, off-diagonal 0.0",
  "symmetric and all values within [-1, 1]; opposite vectors → -1.0",
])
u(5, "F-stage-flow", "S3ObjectStore for artifacts", "store.py", "integration/test_store_s3.py", ["ObjectStore", "S3ObjectStore"], [
  "put_json('artifacts', 'r/chunk/v1.json', {'a': 'ü'}) then get_json → {'a': 'ü'}; raw bytes == b'{\"a\":\"\\xc3\\xbc\"}' (compact, UTF-8)",
  "put_bytes/get_bytes round-trip of PNG bytes",
  "get_bytes missing key in bucket 'artifacts' → WorkerError ARTIFACT_NOT_FOUND details {'key': key}",
  "get_bytes missing key in bucket 'uploads' → WorkerError FILE_NOT_FOUND",
  "bucket that does not exist → WorkerError S3_ERROR",
], intro="Integration test against s3-test (S3_* env). Create buckets 'uploads' and 'artifacts' at test start with aioboto3 if missing.")
u(6, "F-stage-flow", "ApiClient callbacks with retries", "callbacks.py", "unit/test_callbacks.py", ["ApiClient"], [
  "stage_started('id1', ts) → POST {base}/internal/v1/stage-started with JSON {'stage_run_id': 'id1', 'started_at': ts} and header X-Internal-Token",
  "stage_result(body) → POST /internal/v1/stage-results with the body unchanged",
  "put_graph({'stage': 'chunk', 'variant': 'fixed', ...}) → PUT /internal/v1/pipeline-graphs/chunk/fixed",
  "503, 503, 204 → succeeds after 3 calls; recorded sleeps == [1, 2]",
  "five ConnectErrors → raises httpx.ConnectError after 5 attempts; sleeps == [1, 2, 4, 8]",
  "404 → raises httpx.HTTPStatusError after 1 call, no sleep",
  "base_url with trailing slash 'http://api:8000/' builds 'http://api:8000/internal/v1/…'",
], intro="Use respx to mock http://api:8000; pass `sleep=recorder` where `async def recorder(s): sleeps.append(s)`.")
u(7, "F-live-progress", "RedisEventPublisher", "publisher.py", "integration/test_publisher.py", ["EventPublisher", "RedisEventPublisher"], [
  "publish('r1', {'type': 'stage.started', 'x': 'ü'}) → a raw subscriber on 'events:r1' receives a message whose json.loads equals the event",
  "message is compact JSON (no spaces after ':' or ',')",
  "redis client whose publish raises ConnectionError → publish returns without raising",
], intro="Integration test against redis-test (redis.asyncio.from_url(REDIS_URL)).")
u(8, "F-stage-flow", "StageReporter lifecycle", "report.py", "unit/test_reporter.py", ["StageContext", "StageReporter"], [
  "started() → api.started == [(stage_run_id, '2026-11-01T18:22:05.123Z')] (frozen_now) and one stage.started event that validates against contracts events/stage.started.schema.json",
  "progress(1, 4, 'm') then progress(2, 4, 'm') within 0.1 s (fake clock) → only the first published; progress(4, 4, 'm') always published",
  "progress(9, 4, 'm') → done clamped to 4; progress(0, 0, 'm') → nothing published",
  "done(artifact, summary) → artifact stored at '<run_id>/<stage>/v<version>.json' in the artifacts bucket, api.results[0] == {stage_run_id, 'status': 'done', artifact_key, summary, 'error': None, started_at, finished_at}, returns the key",
  "ordering: api.calls ends with ['result', 'stage.completed'] (callback before event)",
  "failed(error_body) → result status failed with error, artifact_key None, summary None; then stage.failed event with the same error",
  "failed when api.fail_results is True → no exception, stage.failed still published",
], intro="Use the `ctx` fixture's FakeApi/FakePublisher/FakeObjectStore and a fake clock `lambda: t[0]`.", deps=["T-worker-005", "T-worker-006", "T-worker-007"])
u(9, "F-stage-flow", "run_stage generic job wrapper", "report.py", "unit/test_run_stage.py", ["run_stage"], [
  "valid payload (FIXTURES/jobs__chunk.json) + body returning ({'a': 1}, {'stage': 'chunk', ...}) → returns {'status': 'done', 'summary': …}; api.results[0].status 'done'; ctx['running'] back to 0",
  "body raising WorkerError('PARSE_FAILED') → {'status': 'failed', 'code': 'PARSE_FAILED'}, failed result with that code",
  "body raising ValueError → failed with code INTERNAL_ERROR and details {'exception': 'ValueError'}",
  "invalid payload (missing stage_run_id) → {'status': 'invalid'}, no api calls",
  "ctx['running'] is 1 while the body runs (body asserts it)",
], intro="Use the `ctx` fixture and JobPayloadChunk from rag_worker.contracts_gen.jobs.chunk_schema.", deps=["T-worker-008"])
u(10, "F-status", "worker heartbeat", "heartbeat.py", "integration/test_heartbeat.py", ["heartbeat_key", "heartbeat_value", "beat_once", "heartbeat_loop"], [
  "beat_once(redis, 'ingest', 'fake', 2) → key 'ragfun:worker:ingest:heartbeat' exists with TTL 25..30 s and JSON value validating events/worker.heartbeat.schema.json with jobs_running 2",
  "heartbeat_loop with interval 0.05 called for ~0.2 s (asyncio.wait_for … cancel) writes the key and uses running() each time",
  "heartbeat_loop survives a redis error on one beat (stub redis raising once) and keeps going",
], intro="Integration test against redis-test.")
u(11, "F-store", "qdrant_admin document_store + deletes", "qdrant_admin.py", "integration/test_qdrant_admin.py", ["document_store", "delete_file_points", "drop_collection"], [
  "document_store(url, name, 4) then write 2 Documents (embedding 4 floats, sparse_embedding, meta file_id 'f1') via store.write_documents → collection has named vectors 'text-dense' size 4 and sparse 'text-sparse' with modifier IDF; payload index 'meta.file_id' exists (keyword)",
  "delete_file_points(client, name, 'f1') → returns 2, count afterwards 0; other file ids untouched",
  "delete_file_points on a missing collection → 0",
  "drop_collection removes it; dropping again does not raise",
], intro=QT)
u(12, "F-embed", "tokenizer loading + real model factories", "models/registry.py", "unit/test_registry.py", ["load_tokenizer", "RealModelSet"], [
  "load_tokenizer('bge-m3').encode('hello world').tokens[0] == '<s>'; load_tokenizer('all-minilm').encode('hi').tokens[0] == '[CLS]'; same object returned twice (cached)",
  "RealModelSet().dense_document_embedder(DenseModelConfig(model='bge-m3', dims=1024, ollama_url='http://o:11434'), 8) is an OllamaDocumentEmbedder with model 'bge-m3', url 'http://o:11434', batch_size 8",
  "sparse_document_embedder('Qdrant/bm25') is a FastembedSparseDocumentEmbedder with model 'Qdrant/bm25'; ranker('Xenova/ms-marco-MiniLM-L-6-v2', 3) is a FastembedRanker with top_k 3",
  "chat_generator(ollama cfg, 0.2, 100) → OllamaChatGenerator, generation_kwargs {'temperature': 0.2, 'num_predict': 100}",
  "chat_generator(anthropic cfg with api_key 'k', ...) → AnthropicChatGenerator; openai_compatible cfg → OpenAIChatGenerator with api_base_url == base_url",
  "no network: constructing every component does not open a socket (use the conftest-free check: monkeypatch socket.create_connection to raise)",
], intro="Unit test; tokenizer files are baked in the image (HF_HUB_OFFLINE=1). Check attributes of the returned components (e.g. `.model`, `.url`, `.top_k`, `.generation_kwargs`).")
u(13, "F-parse", "assign_spans (full_text + char spans)", "components/text_layout.py", "unit/test_text_layout.py", ["assign_spans"], [
  "[text 'A', text 'B'] → full_text 'A\\n\\nB', spans (0,1) and (3,4)",
  "page_header/page_footer and empty-text elements get char_start/char_end None and are not in full_text",
  "input list is not mutated (deep-compare a copy)",
  "unicode text 'čaj' → span length 3",
  "[] → ([], '')",
])
u(14, "F-parse", "PlainTextConverter", "components/plain_text_converter.py", "unit/test_plain_text_converter.py", ["convert_plain", "PlainTextConverter"], [
  "markdown SAMPLES/handbook.md → first element heading 'Employee Handbook' level 1, 'Vacation' level 2, paragraph section_path ['Employee Handbook', 'Vacation']",
  "text/plain notes.txt → 3 text elements (blank-line blocks), ids e-0000..e-0002, pages []",
  "text/csv prices.csv → one table element: num_rows 4, num_cols 3, header cells is_header True, markdown starts '| product | price_eur | plan |'",
  "text/html faq.html → first element text 'FAQ', followed by the two <p> texts",
  "application/pdf q3-report.pdf → 2 text elements with page_no 1 and 2; pages [{page_no 1, width 612, height 792}, …]",
  "image/png → WorkerError UNSUPPORTED_FOR_STRATEGY details {'mime': 'image/png'}; docx mime → same code",
], intro="Read sample bytes from tests.conftest.SAMPLES.", deps=["T-worker-013"])
u(15, "F-parse", "DoclingExtractor (DoclingDocument → elements)", "components/docling_extractor.py", "unit/test_docling_extractor.py", ["extract", "DoclingExtractor"], [
  "DoclingDocument built in the test (doc.add_title('Report'), doc.add_heading('Intro', level=1), doc.add_text(label=DocItemLabel.TEXT, text='Hello'), a 2x2 table via TableData) → element types ['title', 'heading', 'text', 'table'] in order",
  "heading_level: title 1, section_header level 1 → 2; text section_path == ['Report', 'Intro'] (or the heading stack)",
  "table element: table.num_rows 2, num_cols 2, cells with row/col/spans, markdown contains '|'; text == markdown",
  "items with prov on page 1 and a bbox → page_no 1 and bbox {l,t,r,b} with t < b (top-left origin)",
  "unknown label maps to 'text'; DoclingExtractor.run([Document(content=doc.model_dump_json())]) returns the same elements plus docling_json",
], intro="Build documents with docling_core.types.doc (DoclingDocument, DocItemLabel, TableData, TableCell, ProvenanceItem, BoundingBox, Size). No model files needed.")
u(16, "F-parse", "parse pipelines (docling + plain)", "pipelines/parse.py", "integration/test_parse_pipeline.py", ["build_parse_pipeline", "run_parse"], [
  "plain_text pipeline on handbook.md → elements non-empty, page_images {}, docling_json None, ocr_used False",
  "docling_layout on q3-report.pdf (page_images True) → 2 pages, page_images keys {1, 2} with PNG magic bytes, docling_json is a JSON string, 'Revenue grew 12 percent' in some element text",
  "docling_layout with page_images False → page_images {}",
  "docling_ocr on scan-invoice.png → ocr_used True and 'invoice' in joined text (lowercase)",
  "corrupted PDF bytes (b'%PDF-1.4 garbage') → WorkerError PARSE_FAILED",
  "pipeline component names: docling → {'converter', 'extractor'}; plain_text → {'converter'}",
], intro="Uses the real Docling models baked into the worker-dev image (slow: allow ~60 s). Samples in tests.conftest.SAMPLES.", deps=["T-worker-014", "T-worker-015"])
u(17, "F-parse", "parse job", "jobs/parse.py", "integration/test_parse_job.py", ["parse_body"], [
  "ctx store has uploads/<key> = handbook.md bytes; parse({payload from FIXTURES/jobs__parse.json with mime text/markdown, strategy plain_text}) → api.results[0].status done; stored artifact validates artifacts/parse.schema.json; summary {'stage': 'parse', pages 0, elements > 0, tables 0, pictures 0, chars == len(full_text), ocr_used False}",
  "docling_layout on q3-report.pdf → page PNGs stored at keys.page_image_key(run_id, version, n) and artifact pages[].image_key equal to them; docling.json stored at keys.docling_json_key and artifact docling_json_key set",
  "full_text/char spans from assign_spans: every element with spans satisfies full_text[s:e] == text",
  "missing upload object → failed result FILE_NOT_FOUND",
  "plain_text on PNG → failed UNSUPPORTED_FOR_STRATEGY",
  "reporter.progress called at least once (FakePublisher has a stage.progress event)",
], intro="Always: run Haystack pipelines and other CPU work with `await asyncio.to_thread(...)`; read inputs with `ctx['store'].get_json(ctx['settings'].s3_bucket_artifacts, key)` / `get_bytes(ctx['settings'].s3_bucket_uploads, key)`; never call ctx['api'] or ctx['events'] directly except via `rep` (StageReporter); raise WorkerError for expected failures; return (artifact dict, summary dict). Recipe: data = get_bytes(uploads, job.file.s3_key); pipe = pipelines.parse.build_parse_pipeline(job.params.strategy, job.params.model_dump()); res = run_parse(pipe, strategy, data, mime, filename) (to_thread); elements, full_text = components.text_layout.assign_spans(res['elements']); for each page_no, png in res['page_images']: put_bytes(artifacts, keys.page_image_key(job.run_id, job.version, n), png, 'image/png') + rep.progress(i, n, f'page {i}/{n}'); docling_json → put_bytes(artifacts, keys.docling_json_key(...), utf-8, 'application/json'); build the parse artifact (schema_version 1, stage parse, strategy, file_id, mime, ocr_used, pages with image_key or None, elements, full_text, docling_json_key or None); summary pages/elements/tables/pictures (type picture)/chars/ocr_used. " + "Use `ctx` (FakeObjectStore) and call `await parse(ctx, payload)` from rag_worker.jobs.parse.", deps=["T-worker-009", "T-worker-016"])
u(18, "F-chunk", "SemanticSplitter", "components/semantic_splitter.py", "unit/test_semantic_splitter.py", ["breakpoints", "group_sentences", "SemanticSplitter"], [
  "breakpoints([0.1, 0.9, 0.2], 50) → threshold 0.2, is_break [False, True, False]",
  "breakpoints([], 90) == (0.0, [])",
  "group_sentences(4 sentences, [False, True, False], 1, 10) == [[0, 1], [2, 3]]",
  "min_sentences 3 suppresses an early break: is_break [True, False, False], min 3 → [[0, 1, 2, 3]]",
  "max_sentences 2 forces splits: 5 sentences, no breaks → [[0, 1], [2, 3], [4]]",
  "SemanticSplitter(FakeDenseTextEmbedder(64), 50, 1, 10).run([Document(content='Cats purr. Cats sleep. Taxes rise. Taxes hurt.')]) → ≥2 documents whose contents are exact substrings of the input with meta split_idx_start matching; semantic['gaps'] has 3 entries",
])
u(19, "F-chunk", "TableChunker", "components/table_chunker.py", "unit/test_table_chunker.py", ["table_documents", "TableChunker"], [
  "table_documents([table element of FIXTURE-like 2x2 table]) → 1 Document with content == markdown, meta element_type 'table', element_ids [id]",
  "row_chunks True with header ['product','price'] and rows ['Basic','9'], ['Pro','29'] → table doc + 2 row docs 'product: Basic\\nprice: 9' and 'product: Pro\\nprice: 29' with meta no_span True",
  "header cell missing → 'col<N>' label",
  "TableChunker(False, 50, 0).run(elements [text 60 chars, table, text 10 chars], source_text) → documents ordered by position: text chunks, table, text; table chunk split_idx_start == table char_start",
  "no tables → only recursive text chunks",
])
u(20, "F-chunk", "StructureChunker (Docling HybridChunker)", "components/structure_chunker.py", "unit/test_structure_chunker.py", ["TokenizerAdapter", "StructureChunker"], [
  "TokenizerAdapter(load_tokenizer('all-minilm'), 128).count_tokens('hello world') == 2 and get_max_tokens() == 128",
  "StructureChunker(tokenizer, 64, True).run(docling_json of a DoclingDocument with title, 2 headings and 6 paragraphs) → documents; each has meta no_span True and section_path a list of headings",
  "every chunk's token count (adapter) ≤ 64 + heading context",
  "a document with a table item → at least one chunk with element_type 'table' or 'mixed'",
], intro="Build the DoclingDocument in the test with docling_core (no model files). load_tokenizer from rag_worker.models.registry.", deps=["T-worker-012"])
u(21, "F-chunk", "chunk pipelines for 6 strategies", "pipelines/chunk.py", "unit/test_chunk_pipeline.py", ["build_chunk_pipeline", "run_chunk"], [
  "fixed word length 4 overlap 2 on parse artifact FIXTURES/artifact_parse.json → chunks of ≤4 words, consecutive chunks share 2 words, every chunk has a valid span into full_text",
  "fixed char length 10 overlap 0 → every chunk text length ≤ 10 and joined texts == full_text",
  "sentence length 1 → one chunk per sentence; recursive length 80 → every chunk ≤ 80 chars",
  "semantic → result['semantic'] not None with gaps; others → semantic None",
  "structure with docling_json None → WorkerError UNSUPPORTED_FOR_STRATEGY details {'parse_strategy': 'plain_text'}",
  "table strategy on an artifact containing a table element → a chunk with element_type 'table'",
  "pipeline graph names: pipeline.to_dict()['components'] keys == {'splitter', 'annotator'}",
], intro="Use FakeModelSet and DenseModelConfig(model='all-minilm', dims=384, ollama_url='http://x').", deps=["T-worker-018", "T-worker-019", "T-worker-020"])
u(22, "F-chunk", "chunk job", "jobs/chunk.py", "unit/test_chunk_job.py", ["chunk_body"], [
  "parse artifact FIXTURES/artifact_parse.json stored at the payload's parse_artifact_key; chunk(ctx, FIXTURES/jobs__chunk.json payload) → done; artifact validates artifacts/chunk.schema.json; artifact.source_text == parse full_text; parse_strategy copied",
  "summary == {'stage': 'chunk', 'chunks': n, 'min_chars', 'max_chars', 'mean_chars'} consistent with artifact.stats",
  "doc_ids '<file_id>:00000'…; stats from viz.stats.chunk_stats",
  "structure strategy: docling JSON read from the parse artifact's docling_json_key",
  "missing parse artifact → failed ARTIFACT_NOT_FOUND",
], intro="Always: run Haystack pipelines and other CPU work with `await asyncio.to_thread(...)`; read inputs with `ctx['store'].get_json(ctx['settings'].s3_bucket_artifacts, key)` / `get_bytes(ctx['settings'].s3_bucket_uploads, key)`; never call ctx['api'] or ctx['events'] directly except via `rep` (StageReporter); raise WorkerError for expected failures; return (artifact dict, summary dict). Recipe: parse = get_json(artifacts, job.parse_artifact_key); docling_json = get_bytes(artifacts, parse['docling_json_key']).decode() when the key is set else None; pipe = pipelines.chunk.build_chunk_pipeline(strategy, job.params.model_dump(), ctx['models'], job.dense); out = run_chunk(pipe, strategy, parse, docling_json, job.file.file_id) (to_thread); stats = viz.stats.chunk_stats([c['char_count'] for c in chunks]); artifact {schema_version 1, stage chunk, strategy, params (model_dump), parse_strategy = parse['strategy'], source_text = parse['full_text'], chunks, stats, semantic = out['semantic']}; summary {stage, chunks, min_chars, max_chars, mean_chars} from stats. " + "Use `ctx` and put fixtures into ctx['store'] with put_json.", deps=["T-worker-001", "T-worker-009", "T-worker-021"])
u(23, "F-embed", "TokenView component", "components/token_view.py", "unit/test_token_view.py", ["tokenize", "TokenView"], [
  "tokenize(all-minilm tokenizer, 'Hello world', 256) == {'tokens': ['[CLS]', 'hello', 'world', '[SEP]'], 'token_count': 4, 'over_limit': False}",
  "text of 300 words with max_tokens 256 → over_limit True, token_count > 256",
  "very long text → tokens truncated to 2048 entries but token_count is the full count",
  "TokenView.run(documents) returns copies with meta tokens/token_count/over_limit (originals unchanged)",
], deps=["T-worker-012"])
u(24, "F-embed", "embed pipeline + embed artifact", "pipelines/embed.py", "unit/test_embed_pipeline.py", ["build_embed_pipeline", "embed_artifact"], [
  "build_embed_pipeline(collection all-minilm 384, 16, FakeModelSet()).run({'dense': {'documents': docs}}) → documents with embedding (384), sparse_embedding and meta token_count",
  "embed_artifact(those docs, collection, 'sentence-transformers/all-MiniLM-L6-v2', 256) validates artifacts/embed.schema.json",
  "n = 3 chunks → sample_indices [0, 1, 2], similarity 3x3, pca2 3 rows, umap2 None",
  "n = 12 → umap2 and umap3 not None",
  "dense values rounded to 6 decimals",
  "component names {'dense', 'sparse', 'tokens'}",
], deps=["T-worker-002", "T-worker-003", "T-worker-004", "T-worker-023"])
u(25, "F-embed", "embed job", "jobs/embed.py", "unit/test_embed_job.py", ["embed_body"], [
  "chunk artifact FIXTURES/artifact_chunk.json stored; embed(ctx, jobs__embed payload with collection dense all-minilm 384) → done, artifact validates, len(chunks) == 4, doc_ids match the chunk artifact",
  "summary {'stage': 'embed', 'chunks': 4, 'dense_dims': 384, 'mean_tokens' > 0, 'over_limit': 0, 'mean_sparse_nnz' > 0}",
  "progress events emitted per batch (batch_size 2 → done values 2 and 4)",
  "empty chunk list → done with chunks [] and similarity []",
], intro="Always: run Haystack pipelines and other CPU work with `await asyncio.to_thread(...)`; read inputs with `ctx['store'].get_json(ctx['settings'].s3_bucket_artifacts, key)` / `get_bytes(ctx['settings'].s3_bucket_uploads, key)`; never call ctx['api'] or ctx['events'] directly except via `rep` (StageReporter); raise WorkerError for expected failures; return (artifact dict, summary dict). Recipe: chunk = get_json(artifacts, job.chunk_artifact_key); docs = [Document(id=c['doc_id'], content=c['text']) ...]; run the embed pipeline in batches of job.params.batch_size (one pipe.run per batch inside to_thread) calling rep.progress(done_so_far, n, f'embedding {done}/{n}') after each batch; art = pipelines.embed.embed_artifact(all docs, job.collection, repo, max_tokens) with repo/max_tokens from models.registry.TOKENIZERS[job.collection.dense.model]; summary {stage embed, chunks, dense_dims, mean_tokens (round 2), over_limit count, mean_sparse_nnz (round 2)} (0 values for 0 chunks).", deps=["T-worker-009", "T-worker-024"])
u(26, "F-store", "store pipeline + documents_for_store", "pipelines/store.py", "unit/test_store_pipeline.py", ["build_store_pipeline", "documents_for_store"], [
  "documents_for_store(FIXTURES artifact_chunk, artifact_embed, meta_base, ts) → 4 Documents with id == chunk doc_id, embedding == dense, sparse_embedding indices/values, meta validating qdrant/payload.schema.json#/$defs/Meta",
  "meta.page == first page number or None when page_numbers is []",
  "index mismatch (embed artifact with 3 chunks) → WorkerError VALIDATION_ERROR",
  "build_store_pipeline(InMemoryDocumentStore()) writes the documents (store.count_documents() == 4); writing twice keeps 4 (OVERWRITE)",
])
u(27, "F-store", "store job", "jobs/store.py", "integration/test_store_job.py", ["store_body"], [
  "store(ctx, payload) with chunk + embed fixtures → done; Qdrant collection payload.qdrant_name exists with 4 points; artifact validates artifacts/store.schema.json; points_deleted 0",
  "point_ids == [qdrant convert_id(doc_id)] in chunk order; payload_sample validates qdrant/payload.schema.json and meta.tags == payload file tags",
  "running store twice → second artifact points_deleted 4, collection still 4 points",
  "summary {'stage': 'store', 'points_written': 4, 'points_deleted': 0, 'qdrant_collection': name}",
  "Qdrant unreachable (ctx['qdrant_url'] = 'http://127.0.0.1:1') → failed QDRANT_ERROR",
], intro="Always: run Haystack pipelines and other CPU work with `await asyncio.to_thread(...)`; read inputs with `ctx['store'].get_json(ctx['settings'].s3_bucket_artifacts, key)` / `get_bytes(ctx['settings'].s3_bucket_uploads, key)`; never call ctx['api'] or ctx['events'] directly except via `rep` (StageReporter); raise WorkerError for expected failures; return (artifact dict, summary dict). Recipe: chunk = get_json(chunk_artifact_key); emb = get_json(embed_artifact_key); client = QdrantClient(url=ctx['qdrant_url']); deleted = to_thread(qdrant_admin.delete_file_points, client, qdrant_name, file_id) BEFORE writing; ds = qdrant_admin.document_store(ctx['qdrant_url'], qdrant_name, dims) (creates the collection + indexes); docs = pipelines.store.documents_for_store(chunk, emb, meta_base, ids.to_iso(ids.utcnow())) with meta_base from job.file (file_id, batch_id, batch_name, filename, mime, tags) + ingest_run_id = job.run_id, dense_model, sparse_model, parse_strategy, chunk_strategy; run build_store_pipeline(ds) in to_thread; artifact point_ids = [convert_id(d.id) for d in docs] (from haystack_integrations.document_stores.qdrant.converters import convert_id); payload_sample = the payload of chunk 0 as written (= docs[0].to_dict(flatten=False) without embedding/sparse_embedding); vector_config dense_name 'text-dense', dense_size dims, distance 'Cosine', sparse_name 'text-sparse', sparse_modifier 'idf'. Any qdrant_client / connection exception → WorkerError('QDRANT_ERROR'). " + QT + " Use the embed fixture (384 dims) and a collection ref with dims 384.", deps=["T-worker-009", "T-worker-011", "T-worker-026"])
u(28, "F-transform", "transform pipeline + artifact", "pipelines/transform.py", "unit/test_transform_pipeline.py", ["build_transform_pipeline", "transform_artifact"], [
  "transform_artifact('none', q, None, [], None, 3) == queries [q], messages [], model None, hyde_document None",
  "rewrite with reply '  better query \\n second' → queries ['better query']; empty reply → [q]",
  "multi_query reply '1. a\\n- b\\n\\nb\\nq' with question 'q', num 3 → ['q', 'a', 'b'] (prefixes stripped, duplicates and the question removed)",
  "hyde reply ' passage ' → queries ['passage'], hyde_document 'passage'",
  "build_transform_pipeline('multi_query', ollama cfg, FakeModelSet()) runs with {'prompt': {'question': 'q', 'n': 3}} and returns a reply; component names {'prompt', 'llm'}; system prompt contains '3 different search queries'",
  "build_transform_pipeline('none', …) raises ValueError",
])
u(29, "F-transform", "transform job", "jobs/transform.py", "unit/test_transform_job.py", ["transform_body"], [
  "strategy none → done without calling the LLM; artifact queries [question]",
  "multi_query (FakeModelSet) → artifact validates artifacts/transform.schema.json, queries[0] == question, messages[0].role 'system'",
  "hyde → hyde_document == queries[0] == 'Fake answer to: <question> [1]'",
  "summary {'stage': 'transform', 'queries': len(queries)}",
  "chat generator raising RuntimeError → failed LLM_ERROR",
], intro="Always: run Haystack pipelines and other CPU work with `await asyncio.to_thread(...)`; read inputs with `ctx['store'].get_json(ctx['settings'].s3_bucket_artifacts, key)` / `get_bytes(ctx['settings'].s3_bucket_uploads, key)`; never call ctx['api'] or ctx['events'] directly except via `rep` (StageReporter); raise WorkerError for expected failures; return (artifact dict, summary dict). Recipe: strategy none → transform_artifact('none', question, None, [], None, n) without building a pipeline; else pipe = build_transform_pipeline(strategy, job.chat, ctx['models']); res = pipe.run({'prompt': {'question': q, 'n': num_queries}}, include_outputs_from={'prompt'}) in to_thread; reply = res['llm']['replies'][0].text; messages = [{'role': m.role.value, 'content': m.text} for m in res['prompt']['prompt']]; any exception from the run → WorkerError('LLM_ERROR', details={'reason': str(e)[:300]}).", deps=["T-worker-009", "T-worker-028"])
u(30, "F-retrieve", "Hit conversions", "components/hits.py", "unit/test_hits.py", ["to_hit", "hit_to_document"], [
  "to_hit(Document(id=doc_id, content='x', meta=fixture meta, score=0.12345678), 1) → point_id == convert_id(doc_id), rank 1, score 0.123457, validates shared/common.schema.json#/$defs/Hit",
  "explicit score argument wins over doc.score; missing score → 0.0",
  "invalid meta (missing file_id) → pydantic ValidationError",
  "hit_to_document(to_hit(doc, 1)) has the same id, content, meta, score",
])
u(31, "F-retrieve", "RRF fusion", "components/rrf.py", "unit/test_rrf.py", ["rrf_fuse", "RRFJoiner"], [
  "lists dense [A, B], sparse [B, C] with rrf_k 60 → order [B, A, C]; B score round(1/62 + 1/61, 6)",
  "source_ranks of B == [{'query_index': 0, 'list': 'dense', 'rank': 2}, {'query_index': 0, 'list': 'sparse', 'rank': 1}]",
  "ties broken by doc.id ascending",
  "top_k 2 truncates",
  "two queries contribute to the same doc (query_index 0 and 1)",
  "empty input → []",
])
u(32, "F-retrieve", "retrieve pipelines + filters", "pipelines/retrieve.py", "integration/test_retrieve_pipeline.py", ["to_haystack_filters", "build_retrieve_pipeline", "run_retrieve"], [
  "to_haystack_filters(empty) is None",
  "must [tags any ['hr']] → {'operator': 'AND', 'conditions': [{'field': 'meta.tags', 'operator': 'in', 'value': ['hr']}]}",
  "range page gte 1 lte 3 → AND of '>=' 1 and '<=' 3 on 'meta.page'; must_not → {'operator': 'NOT', ...}",
  "hybrid over a seeded Qdrant collection (3 docs written with fake dense/sparse embeddings via qdrant_admin.document_store) → per query both dense and sparse lists non-empty; best dense hit for 'vacation days' is the vacation doc",
  "filters tags ['tax'] → every returned doc has meta.tags ['tax']",
  "mode dense → sparse None; mode sparse → dense None; component names for hybrid include 'dense_retriever' and 'sparse_retriever'",
], intro=QT + " Seed with FakeModelSet embedders (dims 16).", deps=["T-worker-011"])
u(33, "F-retrieve", "retrieve job", "jobs/retrieve.py", "integration/test_retrieve_job.py", ["retrieve_body"], [
  "with a seeded collection and transform_artifact_key None → per_query has 1 entry with query == question; artifact validates artifacts/retrieve.schema.json",
  "with a transform artifact (multi_query, 3 queries) → per_query length 3; fused deduplicated by doc_id",
  "fused hits ranks 1..n and source_ranks set; summary {'stage': 'retrieve', 'queries': n, 'hits': len(fused)}",
  "mode dense → fused == dense list re-ranked, sparse None",
  "collection never stored (document_store creates it empty) → status done, per_query[0].dense == [] and fused == []",
], intro="Always: run Haystack pipelines and other CPU work with `await asyncio.to_thread(...)`; read inputs with `ctx['store'].get_json(ctx['settings'].s3_bucket_artifacts, key)` / `get_bytes(ctx['settings'].s3_bucket_uploads, key)`; never call ctx['api'] or ctx['events'] directly except via `rep` (StageReporter); raise WorkerError for expected failures; return (artifact dict, summary dict). Recipe: queries = transform artifact['queries'] if job.transform_artifact_key else [job.question]; ds = qdrant_admin.document_store(qdrant_url, qdrant_name, dims); pipe = build_retrieve_pipeline(mode, collection, ds, top_k, ctx['models']); per = run_retrieve(pipe, mode, queries, to_haystack_filters(job.params.filters)) in to_thread; per_query entries convert Documents with components.hits.to_hit(doc, rank); lists for RRF = [(qi, 'dense', docs), (qi, 'sparse', docs)] for every non-None list; fused = rrf_fuse(lists, rrf_k, top_k) → [{'hit': to_hit(doc, rank i+1, score), 'source_ranks'}]; for mode dense/sparse with ONE query fused = that list re-ranked 1..n keeping the original scores (source_ranks from that list). " + QT, deps=["T-worker-009", "T-worker-030", "T-worker-031", "T-worker-032"])
u(34, "F-rerank", "rerank pipeline + artifact", "pipelines/rerank.py", "unit/test_rerank_pipeline.py", ["build_rerank_pipeline", "rerank_artifact"], [
  "rerank_artifact(True, model, 2, q, before=FIXTURES artifact_retrieve fused hits, reranked docs [d3, d1] with scores 0.9, 0.5) → after[0].hit.doc_id == d3, previous_rank == rank of d3 in before, rerank_score 0.9, hit.rank 1",
  "disabled → after == before[:top_n] with previous_rank == rank, rerank_score None, model None",
  "artifact validates artifacts/rerank.schema.json",
  "build_rerank_pipeline(model, 2, FakeModelSet()).run({'ranker': {'query': 'tax refund', 'documents': docs}}) → 2 docs, best overlap first; component names {'ranker'}",
], deps=["T-worker-030"])
u(35, "F-rerank", "rerank job", "jobs/rerank.py", "unit/test_rerank_job.py", ["rerank_body"], [
  "retrieve artifact fixture stored; rerank(ctx, jobs__rerank payload enabled top_n 2) → done, after length 2, artifact validates",
  "enabled False → after order equals before order",
  "summary {'stage': 'rerank', 'enabled': True, 'in': len(before), 'out': 2}",
  "missing retrieve artifact → failed ARTIFACT_NOT_FOUND",
], intro="Always: run Haystack pipelines and other CPU work with `await asyncio.to_thread(...)`; read inputs with `ctx['store'].get_json(ctx['settings'].s3_bucket_artifacts, key)` / `get_bytes(ctx['settings'].s3_bucket_uploads, key)`; never call ctx['api'] or ctx['events'] directly except via `rep` (StageReporter); raise WorkerError for expected failures; return (artifact dict, summary dict). Recipe: ret = get_json(retrieve_artifact_key); before = [f['hit'] for f in ret['fused']]; enabled → pipe = build_rerank_pipeline(job.model, top_n, ctx['models']); docs = pipe.run({'ranker': {'query': job.question, 'documents': [hit_to_document(h) for h in before]}})['ranker']['documents'] in to_thread; art = rerank_artifact(enabled, model or None, top_n, question, before, docs or None).", deps=["T-worker-009", "T-worker-034"])
u(36, "F-generate", "context selection + citation parsing", "components/context_builder.py", "unit/test_context_builder.py", ["select_context", "parse_citations"], [
  "select_context([h1, h2, h3], [100, 50, 30], 140) → h1 fits (100), h2 does not (150 > 140, dropped), h3 fits (130) → included [{n 1, hit h1, tokens 100}, {n 2, hit h3, tokens 30}], used 130, dropped 1",
  "budget 0 → included [], used 0, dropped 3",
  "parse_citations('A [1] b [2, 3] c [3] d [9]', 3) == [1, 2, 3]",
  "parse_citations('[1,2]', 1) == [1]; parse_citations('no cites', 5) == []",
])
u(37, "F-generate", "generate pipeline + artifact", "pipelines/generate.py", "unit/test_generate_pipeline.py", ["build_generate_pipeline", "generate_artifact"], [
  "build_generate_pipeline(ollama cfg, 0.2, 100, FakeModelSet(), cb).run({'prompt': {'context': [{'n': 1, 'text': 'x'}], 'question': 'q'}}) → replies[0].text == 'Fake answer to: Context: [1]' (first line of the user message is 'Context:'); the streaming callback chunks join to that text; component names {'prompt', 'llm'}",
  "the user message contains '[1] x' and 'Question: q'; system message == prompts.ANSWER_SYSTEM",
  "generate_artifact(..., answer 'a [1] [2]', context of 1) → citations [1]; validates artifacts/generate.schema.json",
  "usage passed through (None values allowed)",
], deps=["T-worker-036"])
u(38, "F-generate", "generate job with streaming", "jobs/generate.py", "unit/test_generate_job.py", ["generate_body"], [
  "rerank artifact fixture stored, payload context_source 'rerank' → done; context hits == rerank after hits (n 1..k) within budget; artifact validates",
  "context_source 'retrieve' uses retrieve fused hits",
  "generate.token events published with contiguous index from 0 and texts joining to the answer",
  "budget: system_tokens + question_tokens counted with the bge-m3 tokenizer; used_context_tokens ≤ max_context_tokens",
  "summary {'stage': 'generate', 'answer_chars': len(answer), 'citations': 1, 'chunks_included': k, 'prompt_tokens', 'completion_tokens'} from fake usage",
  "LLM error → failed LLM_ERROR",
], intro="Always: run Haystack pipelines and other CPU work with `await asyncio.to_thread(...)`; read inputs with `ctx['store'].get_json(ctx['settings'].s3_bucket_artifacts, key)` / `get_bytes(ctx['settings'].s3_bucket_uploads, key)`; never call ctx['api'] or ctx['events'] directly except via `rep` (StageReporter); raise WorkerError for expected failures; return (artifact dict, summary dict). Recipe: src = get_json(job.context_artifact_key); hits = [a['hit'] for a in src['after']] if context_source == 'rerank' else [f['hit'] for f in src['fused']]; tok = ctx['models'].tokenizer('bge-m3'); counts = [len(tok.encode(h['content'], add_special_tokens=False).ids)]; system/question tokens likewise for prompts.ANSWER_SYSTEM and the question; included, used, dropped = select_context(hits, counts, max_context_tokens); loop = asyncio.get_running_loop(); callback(chunk) → asyncio.run_coroutine_threadsafe(ctx['events'].publish(job.run_id, generate.token event with contiguous index), loop); pipe = build_generate_pipeline(job.chat, temperature, max_answer_tokens, ctx['models'], callback); res = pipe.run({'prompt': {'context': [{'n': c['n'], 'text': c['hit']['content']} ...], 'question': q}}, include_outputs_from={'prompt'}) in to_thread; usage from replies[0].meta['usage'] (prompt_tokens/completion_tokens, None when missing); LLM exception → WorkerError('LLM_ERROR'). " + "Streaming callbacks run in a worker thread (pipeline.run inside asyncio.to_thread): publish tokens via asyncio.run_coroutine_threadsafe(events.publish(...), loop) captured before to_thread.", deps=["T-worker-009", "T-worker-037"])
u(39, "F-pipeline-graph", "pipeline graph export", "pipelines/graphs.py", "unit/test_graphs.py", ["graph_of", "all_graphs"], [
  "all_graphs(FakeModelSet(), 'http://127.0.0.1:1') returns 19 graphs in VARIANTS order, each validating shared/pipeline-graph.schema.json, without network (socket guard)",
  "chunk/semantic graph has node 'splitter' with custom True and type ending 'SemanticSplitter'; edge splitter.documents → annotator.documents",
  "retrieve/hybrid nodes include dense_embedder, dense_retriever, sparse_embedder, sparse_retriever",
  "init param named 'api_key' (anthropic chat cfg in a graph_of call) → value '\"***\"'",
  "nodes sorted by name",
], deps=["T-worker-016", "T-worker-021", "T-worker-024", "T-worker-026", "T-worker-028", "T-worker-032", "T-worker-034", "T-worker-037"])
u(40, "F-collections", "maintenance jobs drop_collection + delete_points", "jobs/maintenance.py", "integration/test_maintenance_jobs.py", ["drop_collection", "delete_points"], [
  "delete_points(ctx, {'qdrant_name': n, 'file_id': f}) on a seeded collection → {'status': 'done', 'deleted': k}; no api/events calls",
  "drop_collection(ctx, {'qdrant_name': n}) → collection gone, {'status': 'done'}",
  "invalid payload → {'status': 'failed'} without raising",
  "Qdrant unreachable → {'status': 'failed'}",
], intro=QT, deps=["T-worker-011"])
