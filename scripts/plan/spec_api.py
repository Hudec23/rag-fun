from core import unit, py_ctx

S = "services/api/src/rag_api/"
T = "services/api/tests/"
def u(num, feat, title, src, test, names, cases, **kw):
    ctx = kw.pop("ctx", None) or py_ctx(S + src, names, kw.pop("intro", ""))
    return unit("api", num, feat, title, S + src, T + test, ctx, cases, **kw)

INFRA = "Integration test: uses the `session`/`client` fixtures (postgres-test)."
u(1, "F-upload", "tag helpers normalize_tags + parse_tags_csv", "services/tags.py", "unit/test_tags.py", ["normalize_tags", "parse_tags_csv"], [
  "normalize_tags(['b', 'a', 'b']) == ['a', 'b']",
  "normalize_tags([]) == []",
  "parse_tags_csv('finance, q3,,Q3 ') == ['finance', 'q3']",
  "parse_tags_csv(None) == [] and parse_tags_csv('') == []",
  "parse_tags_csv('ok,Bad Tag!') raises AppError code VALIDATION_ERROR with details == {'field': 'tags'}",
  "parse_tags_csv('a'*65) raises VALIDATION_ERROR",
  "parse_tags_csv(','.join(f't{i}' for i in range(33))) raises VALIDATION_ERROR (33 > 32 tags)",
  "parse_tags_csv('v1.2:beta_x-y') == ['v1.2:beta_x-y'] (all allowed characters)",
])
u(2, "F-stage-flow", "validate_stage_params cross-field rules", "services/validation.py", "unit/test_validation.py", ["validate_stage_params"], [
  "chunk fixed length 10 overlap 9 → no error (returns None)",
  "chunk fixed length 10 overlap 10 → AppError VALIDATION_ERROR details {'field': 'params.overlap'}",
  "chunk sentence length 2 overlap 3 → VALIDATION_ERROR field params.overlap",
  "chunk recursive length 100 overlap 100 → VALIDATION_ERROR field params.overlap",
  "chunk table text_length 50 text_overlap 50 → VALIDATION_ERROR field params.text_overlap",
  "chunk semantic min_sentences 5 max_sentences 4 → VALIDATION_ERROR field params.min_sentences; min 4 max 4 → ok",
  "chunk structure {'strategy': 'structure', 'max_tokens': 64, 'merge_peers': True} → ok",
  "stage 'parse' and 'embed' with any params → ok",
])
u(3, "F-upload", "S3ObjectStore (aioboto3 against RustFS)", "s3.py", "integration/test_s3_store.py", ["ObjectStore", "ObjectNotFound", "S3ObjectStore"], [
  "S3ObjectStore(settings).ensure_bucket('t-<random hex>') then head_bucket(same) succeeds; ensure_bucket twice does not raise",
  "put_bytes(bucket, 'a/b.txt', b'hello', 'text/plain') then get_bytes == b'hello'",
  "get_bytes(bucket, 'missing.txt') raises ObjectNotFound",
  "delete(bucket, 'a/b.txt') then get_bytes raises ObjectNotFound; deleting a missing key does not raise",
  "head_bucket('no-such-bucket-<hex>') raises AppError with code S3_ERROR",
  "keys with unicode 'ünï/čo.pdf' round-trip",
], intro="Integration test against s3-test (S3_ENDPOINT_URL). Use a fresh bucket name per test (e.g. 't-' + uuid4().hex[:8]). Use the `settings` fixture.",
   steps=["aioboto3.Session().client('s3', endpoint_url=settings.s3_endpoint_url, aws_access_key_id=…, aws_secret_access_key=…, region_name='us-east-1') as an async context manager per call.",
          "Map botocore ClientError code NoSuchKey/404 in get_bytes to ObjectNotFound; every other ClientError/EndpointConnectionError to AppError('S3_ERROR', details={'bucket': bucket}).",
          "ensure_bucket: head_bucket, create_bucket on 404."])
u(4, "F-stage-flow", "ArqJobQueue.enqueue", "queue.py", "integration/test_queue.py", ["JobQueue", "ArqJobQueue"], [
  "enqueue('chunk', {'stage_run_id': 'x1', 'a': 1}, 'ingest') with an ArqRedis from arq.create_pool(RedisSettings.from_dsn(REDIS_URL)) → a job with function 'chunk' is in queue 'ingest' (pool.queued_jobs(queue_name='ingest')) whose args == ({'stage_run_id': 'x1', 'a': 1},)",
  "job id equals payload['stage_run_id'] ('x1')",
  "enqueuing the same stage_run_id twice leaves exactly one queued job",
  "payload without stage_run_id (e.g. drop_collection {'qdrant_name': 'rf_…'}) is enqueued on queue 'query' with a generated id",
], intro="Integration test against redis-test (REDIS_URL env). Flush the db (await pool.flushdb()) at the start of each test.")
u(5, "F-live-progress", "RedisEventBus publish/subscribe", "events.py", "integration/test_event_bus.py", ["EventBus", "RedisEventBus"], [
  "publish(run_id, {'type': 'run.updated', 'x': 1}) → a raw redis subscriber on 'events:<run_id>' receives the JSON string that json.loads to the same dict",
  "subscribe(run_id) yields events published after subscribing, in order (publish two, read two with asyncio.wait_for 5 s)",
  "events published on another run's channel are not yielded",
  "a non-JSON message published raw on the channel is skipped, the next valid event is still yielded",
], intro="Integration test against redis-test: `redis.asyncio.from_url(os.environ['REDIS_URL'])`. subscribe must use redis pubsub on channel events.channel(run_id) and json.loads each message.")
u(6, "F-qdrant-browser", "to_qdrant_filter", "qdrant_read.py", "unit/test_qdrant_filter.py", ["to_qdrant_filter"], [
  "PayloadFilter() (empty) → None; PayloadFilter(must=[]) → None",
  "must [{key: tags, match: {any: ['hr']}}] → models.Filter(must=[FieldCondition(key='meta.tags', match=MatchAny(any=['hr']))])",
  "must [{key: file_id, match: {value: 'abc'}}] → FieldCondition(key='meta.file_id', match=MatchValue(value='abc'))",
  "must [{key: page, range: {gte: 1, lte: 3}}] → FieldCondition(key='meta.page', range=Range(gte=1, lte=3)); only gte given → lte None",
  "should and must_not lists map to Filter.should / Filter.must_not with the same conversion",
], intro="Build inputs with `PayloadFilter.model_validate({...})` (from rag_api.contracts_gen.shared.common_schema import PayloadFilter). Compare with `qdrant_client.models` objects using ==.")
u(7, "F-qdrant-browser", "QdrantReader info/scroll/count/facet/get_point", "qdrant_read.py", "integration/test_qdrant_reader.py", ["QdrantReader"], [
  "info on a missing collection → QdrantInfo(qdrant_name, exists=False, status=None, points_count=None, dense=None, sparse=None, payload_indexes=[])",
  "seed: create collection 'rf_<32 hex>' with vectors {'text-dense': VectorParams(size=4, distance=COSINE)}, sparse {'text-sparse': SparseVectorParams(modifier=IDF)}, keyword index meta.tags, 3 points (payload = contract payload fixture with meta.tags ['hr'], ['hr'], ['tax']); info → exists True, points_count 3, dense == DenseInfo(name='text-dense', size=4, distance='Cosine'), sparse.modifier 'idf', payload_indexes contains key 'meta.tags' type 'keyword'",
  "scroll(filter tags any ['hr'], limit 1, offset None, with_vectors False) → 1 point, vectors None, next_offset not None; second page with that offset → 1 point, next_offset None",
  "scroll with_vectors True → vectors.dense has 4 floats, vectors.sparse.indices non-empty",
  "count(empty filter) == 3; count(tags ['tax']) == 1; count on missing collection == 0",
  "facet('tags') → values [{'value': 'hr', 'count': 2}, {'value': 'tax', 'count': 1}] (count desc)",
  "get_point(existing id) → payload equals seeded payload; get_point(unknown 32-hex id) raises AppError POINT_NOT_FOUND",
], intro="Integration test against qdrant-test (QDRANT_URL) with qdrant_client.AsyncQdrantClient; collection name 'rf_' + uuid4().hex, delete it after the test. Point ids are 32-hex strings; payload from tests.conftest.FIXTURES / 'qdrant__payload.json'.",
   deps=["T-api-006"], tdeps=["T-api-006"])
u(8, "F-upload", "upload_batch + detect_mime + default_batch_name", "services/uploads.py", "integration/test_uploads.py", ["detect_mime", "default_batch_name", "upload_batch"], [
  "detect_mime('Report.PDF') == 'application/pdf'; 'a.jpeg' → 'image/jpeg'; 'x.tif' → 'image/tiff'",
  "detect_mime('notes.rtf') and detect_mime('README') raise AppError UNSUPPORTED_FILE_TYPE with details {'filename': …}",
  "default_batch_name('2026-11-01T18:22:05.123Z') == 'Batch 2026-11-01 18:22'",
  "upload_batch with 2 files (a.md, b.pdf), name None, tags ['x'] (frozen_now) → batch.name 'Batch 2026-11-01 18:22', tags ['x'], file_count 2; files in order with sha256 hex of each payload; store.objects has keys f'{batch_id}/{file_id}/a.md' in bucket 'uploads' with content type 'text/markdown'",
  "0 files → EMPTY_UPLOAD; 21 files (max_files_per_batch 20) → TOO_MANY_FILES details {'limit': 20}",
  "second file > max_upload_mb (monkeypatch settings.max_upload_mb = 0 makes 1 byte too large) → FILE_TOO_LARGE details {'filename': 'b.pdf', 'limit_mb': 0} and store.objects is empty, no batch row",
  "one unsupported extension among valid files → UNSUPPORTED_FILE_TYPE and nothing stored",
  "empty file (0 bytes) → VALIDATION_ERROR details {'field': 'files', 'filename': …}",
], intro=INFRA, deps=["T-api-001", "T-api-003"])
u(9, "F-upload", "batches list/get/update", "services/batches.py", "integration/test_batches.py", ["batch_out", "file_out", "list_batches", "get_batch", "update_batch"], [
  "list_batches with 3 batches created at t1<t2<t3 (insert BatchRow/FileRow directly) → items newest first, file_count per batch correct, page {total 3, limit 2, offset 0} when limit=2",
  "list_batches offset beyond total → items [] and total unchanged",
  "get_batch → files ordered by created_at asc; timestamps formatted '2026-11-01T18:22:05.123Z'",
  "get_batch(unknown id) → AppError BATCH_NOT_FOUND details {'batch_id': id}",
  "update_batch(tags ['b','a','a']) → tags ['a','b']; name unchanged",
  "update_batch(BatchUpdate()) → VALIDATION_ERROR details {'field': 'body'}",
], intro=INFRA, deps=["T-api-001"])
u(10, "F-upload", "files list/get/update/delete/content", "services/files.py", "integration/test_files.py", ["list_files", "get_file", "update_file", "delete_file", "get_file_content"], [
  "list_files filters: batch_id only, tag 'tax' (files.tags contains), mime 'text/plain', and all three AND-ed; page.total counts filtered rows",
  "list_files order: created_at desc then filename asc (two files with the same created_at sorted by name)",
  "get_file unknown → FILE_NOT_FOUND details {'file_id'}",
  "update_file(tags ['z','a','z']) → tags ['a','z']",
  "delete_file: file with a done store stage run in collection C → queue.jobs == [('delete_points', {'qdrant_name': C.qdrant_name, 'file_id': id}, 'query')], file row and its ingest + stage rows gone, upload object removed from store",
  "delete_file of a file never stored → no jobs enqueued",
  "get_file_content returns (bytes, mime, filename) from the store",
], intro=INFRA, deps=["T-api-001", "T-api-009"])
u(11, "F-collections", "create_collection + delete_collection", "services/collections.py", "integration/test_collections_write.py", ["create_collection", "delete_collection"], [
  "create_collection(name 'exp', dense 'nomic-embed-text', sparse 'Qdrant/bm25') with frozen_now → dense_dims 768, qdrant_name 'rf_' + id without dashes, created_at '2026-11-01T18:22:05.123Z'",
  "dense 'all-minilm' → dims 384; 'mxbai-embed-large' → 1024",
  "same name twice → AppError COLLECTION_NAME_TAKEN details {'name': 'exp'}",
  "delete_collection: row removed, its ingest runs + query runs + their stage runs removed, queue.jobs == [('drop_collection', {'qdrant_name': …}, 'query')]",
  "delete_collection(unknown) → COLLECTION_NOT_FOUND, no job enqueued",
], intro=INFRA)
u(12, "F-settings", "app settings get/put/resolve", "services/app_settings.py", "integration/test_app_settings.py", ["mask_key", "load_value", "get_settings_out", "put_settings", "resolve_chat", "ollama_url", "reranker_model"], [
  "mask_key(None) is None; mask_key('') is None; mask_key('abc') == '…bc'; mask_key('sk-ant-secret-abcd') == 'sk-…abcd'",
  "get_settings_out with add_settings default → chat_provider 'ollama', anthropic.api_key_set False, api_key_masked None",
  "put_settings anthropic with api_key 'sk-ant-secret-abcd' → api_key_set True, masked 'sk-…abcd'; stored value keeps the full key",
  "put_settings with api_key None keeps the stored key; with '' removes it",
  "chat_provider 'anthropic' and no key (none stored) → VALIDATION_ERROR details {'field': 'anthropic.api_key'}",
  "chat_provider 'openai_compatible' without base_url → field 'openai_compatible.base_url'; with base_url but no model → 'openai_compatible.model'",
  "resolve_chat: ollama → {'provider': 'ollama', 'model': 'qwen3:8b', 'base_url': ollama.url, 'api_key': None}; anthropic → base_url None + stored key; openai_compatible → base_url + key",
  "load_value without a settings row → AppError INTERNAL_ERROR",
], intro=INFRA)
u(13, "F-stage-flow", "stage state machine (latest/active/downstream/check/stale/start_stage)", "services/stages.py", "integration/test_stages.py",
  ["run_kind_of", "stage_run_out", "latest_rows", "active_row", "downstream_of", "check_can_start", "mark_stale", "start_stage"], [
  "downstream_of('chunk') == ['embed', 'store']; downstream_of('store') == []; downstream_of('transform') == ['retrieve', 'rerank', 'generate']",
  "latest_rows returns the highest version per stage (rows v1 done, v2 failed for parse → v2)",
  "active_row: latest done → that row; latest failed/stale/queued → None",
  "check_can_start('chunk') with no parse → AppError STAGE_PREREQUISITE_MISSING details {'stage': 'chunk', 'missing': 'parse'}; parse latest running → still missing",
  "check_can_start('parse') when parse latest is queued → STAGE_ALREADY_RUNNING details {'stage': 'parse'}",
  "check_can_start('retrieve') with nothing run → ok; 'generate' without retrieve → missing 'retrieve'",
  "mark_stale('parse') with chunk done, embed failed, store queued → chunk + embed set stale, returns ['chunk', 'embed'], store untouched",
  "start_stage (monkeypatch job_payloads.build_payload to return {'p': 1}) on an ingest run → row version 1 status queued; queue.jobs == [('parse', {'p': 1}, 'ingest')]; bus published run.updated reason 'stage_queued' with run_kind 'ingest'",
  "start_stage parse again after v1 done with chunk done → version 2, chunk latest stale, bus reasons ['stage_queued', 'stages_stale']",
  "start_stage clears run.run_all_plan unless keep_plan=True",
  "stage_run_out formats timestamps with to_iso and keeps None",
], intro=INFRA + " Create runs by inserting FileRow/BatchRow/IngestRunRow/QueryRunRow/StageRunRow directly.", deps=["T-api-004", "T-api-005"])
u(14, "F-stage-flow", "build_payload for all 8 stages", "services/job_payloads.py", "integration/test_job_payloads.py", ["envelope", "file_block", "build_payload"], [
  "envelope(row) == {'stage_run_id', 'run_id', 'run_kind', 'stage', 'version'} from the row",
  "file_block: tags = sorted union of file tags ['b'] and batch tags ['a','b'] → ['a','b']; s3_key and batch_name copied",
  "parse payload validates against contracts jobs/parse.schema.json (errors(payload, 'jobs/parse.schema.json') == [])",
  "chunk payload: parse_artifact_key = active parse row's artifact_key; dense == {'model': 'bge-m3', 'dims': 1024, 'ollama_url': settings ollama url}; validates",
  "embed + store payloads validate; store parse_strategy/chunk_strategy come from the active parse/chunk params",
  "transform/generate payload 'chat' == app_settings.resolve_chat; generate context_source 'rerank' when rerank active else 'retrieve' with the matching artifact key",
  "retrieve payload transform_artifact_key None when transform never ran; rerank payload model == settings reranker_model",
], intro=INFRA + " Insert stage rows with status done and artifact_key set to simulate active upstream stages; use add_settings + add_collection.", deps=["T-api-012", "T-api-013"])
u(15, "F-stage-flow", "run-all plans", "services/run_all.py", "integration/test_run_all.py", ["first_not_done", "start_run_all", "advance_plan"], [
  "first_not_done(['parse','chunk','embed','store'], {}) == 'parse'; {'parse': 'done', 'chunk': 'failed'} → 'chunk'; all done → None",
  "start_run_all(ingest run, None, params) with nothing run → returns True, queue.jobs[0][0] == 'parse', run.run_all_plan == [{'stage': 'chunk', 'params': …}, {'stage': 'embed', …}, {'stage': 'store', …}]",
  "start_run_all with from_stage 'embed' (chunk done) → starts embed, plan == [store]",
  "start_run_all with every stage done and from_stage None → returns False, no jobs",
  "advance_plan pops the first entry and starts it (queue gets 'chunk'), plan shrinks by one",
  "advance_plan with an empty plan does nothing",
  "advance_plan when the next stage cannot start (prerequisite missing) → plan cleared, no exception",
], intro=INFRA + " Monkeypatch job_payloads.build_payload to return {} so only the plan logic is tested.", deps=["T-api-013"])
u(16, "F-stage-flow", "ingest runs create/get/list/batch ingest", "services/ingest_runs.py", "integration/test_ingest_runs.py", ["load_ingest_run", "ingest_run_out", "create_ingest_run", "list_ingest_runs", "ingest_batch"], [
  "create_ingest_run → IngestRunOut with file (FileOut), stages all None, run_all_pending []",
  "create with unknown file → FILE_NOT_FOUND; known file + unknown collection → COLLECTION_NOT_FOUND",
  "ingest_run_out shows latest row per stage and run_all_pending == [p['stage'] for p in plan]",
  "list_ingest_runs filters by file_id and collection_id, newest first, page total",
  "ingest_batch with 2 files → 2 runs, each has a queued parse stage, queue.jobs functions == ['parse', 'parse']",
  "load_ingest_run(unknown) → RUN_NOT_FOUND details {'run_id'}",
], intro=INFRA + " Monkeypatch job_payloads.build_payload to return {}.", deps=["T-api-010", "T-api-015"])
u(17, "F-transform", "query runs create/get/list", "services/query_runs.py", "integration/test_query_runs.py", ["load_query_run", "query_run_out", "create_query_run", "list_query_runs"], [
  "create_query_run(collection, '  How?  ') → question 'How?', stages all None",
  "create with question '   ' → VALIDATION_ERROR details {'field': 'question'}",
  "unknown collection → COLLECTION_NOT_FOUND",
  "query_run_out shows latest rows per query stage",
  "list_query_runs by collection_id newest first",
  "load_query_run(an ingest run id) → RUN_NOT_FOUND",
], intro=INFRA, deps=["T-api-013"])
u(18, "F-stage-flow", "worker callbacks record_started + record_result", "services/results.py", "integration/test_results.py", ["record_started", "record_result"], [
  "record_started on a queued row → status running, started_at set; on a done row → unchanged",
  "record_result done → status done, artifact_key, summary, finished_at stored; bus run.updated reason 'stage_result'",
  "record_result failed → status failed, error stored, run.run_all_plan cleared",
  "record_result for a row already done → ignored (summary unchanged, no event)",
  "record_result done with a run-all plan [chunk] → chunk queued (monkeypatch job_payloads.build_payload → {}), plan []",
  "unknown stage_run_id → STAGE_RUN_NOT_FOUND",
  "HTTP: POST /internal/v1/stage-results without X-Internal-Token → 401 UNAUTHORIZED; with token and the contract example (tests.conftest.FIXTURES / … build from contracts/openapi/internal.yaml example) → 204",
], intro=INFRA, deps=["T-api-015"])
u(19, "F-stage-flow", "stage runs + artifact proxy + page images", "services/artifacts.py", "integration/test_artifacts.py", ["get_stage_run", "list_stage_runs", "get_artifact", "get_page_image"], [
  "get_stage_run unknown → STAGE_RUN_NOT_FOUND",
  "list_stage_runs returns versions desc; unknown run → empty items",
  "get_artifact returns the stored bytes unchanged (store.objects[('artifacts', key)])",
  "get_artifact with artifact_key None → ARTIFACT_NOT_FOUND; key set but object missing → ARTIFACT_NOT_FOUND",
  "get_page_image: parse artifact (FIXTURES/artifact_parse.json) stored under the row key and b'\\x89PNG' at its page 1 image_key → returns the PNG bytes",
  "get_page_image page 9 / non-parse stage / image_key None → PAGE_NOT_FOUND details {'page_no': n}",
], intro=INFRA)
u(20, "F-live-progress", "SSE message mapping", "services/sse.py", "unit/test_sse.py", ["sse_messages"], [
  "FakeEventBus publish {'type': 'stage.started', 'run_id': 'r'} after subscribing → first yielded item == {'event': 'stage.started', 'data': '{\"type\":\"stage.started\",\"run_id\":\"r\"}'}",
  "events without 'type' or with non-str type are skipped",
  "events of other run ids are not yielded",
  "unicode in event data is preserved (json.loads(item['data']) equals the event)",
], intro="Unit test with tests.fakes.FakeEventBus; consume with `agen = sse_messages(bus, 'r')`; `await asyncio.wait_for(agen.__anext__(), 2)` after publishing from another task (publish after a `await asyncio.sleep(0)` so the subscription exists).", deps=["T-api-005"])
u(21, "F-qdrant-browser", "qdrant browser service", "services/qdrant_browser.py", "integration/test_qdrant_browser_service.py", ["info", "scroll", "count", "facet", "get_point"], [
  "info(unknown collection id) → COLLECTION_NOT_FOUND",
  "info delegates to reader.info(row.qdrant_name) (use a stub reader class recording calls)",
  "scroll passes filter, limit, offset, with_vectors through and returns the reader's ScrollResponse",
  "count returns CountResponse(count=reader result)",
  "reader raising a generic Exception → AppError QDRANT_ERROR; reader raising AppError POINT_NOT_FOUND → propagated unchanged",
], intro=INFRA + " Use a small stub class in the test implementing QdrantReader's methods (no real Qdrant).", deps=["T-api-007"])
u(22, "F-settings", "test_connection probes", "services/connection_test.py", "integration/test_connection_probe.py", ["test_connection"], [
  "ollama: respx GET http://ollama-fake:11434/api/tags → {'models': [{'name': 'qwen3:8b'}]} → ok True, models ['qwen3:8b'], latency_ms ≥ 0",
  "ollama connect error (respx side_effect httpx.ConnectError('x')) → ok False, detail contains 'x', models []",
  "anthropic with stored key: GET https://api.anthropic.com/v1/models has headers x-api-key and anthropic-version '2023-06-01', response {'data': [{'id': 'claude-sonnet-5-5'}]} → models ['claude-sonnet-5-5']",
  "anthropic without key → ok False, detail 'not configured', latency_ms 0, no HTTP call",
  "openai_compatible override base_url 'http://lm:1234/v1' + key 'k' → GET http://lm:1234/v1/models with Authorization 'Bearer k'",
  "HTTP 401 → ok False, detail 'HTTP 401'",
], intro=INFRA + " Mock HTTP with respx (`respx.mock` decorator/context). Pass `httpx.AsyncClient()` as http.", deps=["T-api-012"])
u(23, "F-status", "status of all components", "services/status.py", "integration/test_status_service.py", ["get_status"], [
  "all healthy (stub redis with async ping/exists returning True, FakeObjectStore with bucket uploads, stub qdrant reader whose client.get_collections returns [], respx ollama 200) → 8 components in order api, worker-ingest, worker-query, postgres, redis, qdrant, s3, ollama, all ok, detail None",
  "redis exists False for 'ragfun:worker:query:heartbeat' → worker-query ok False detail 'heartbeat missing'",
  "store.fail = True → s3 ok False with detail text",
  "ollama ConnectError → ollama ok False, others still ok",
  "a check that hangs (stub awaits asyncio.sleep(10)) is reported not ok within ~2 s (assert total time < 5 s)",
], intro=INFRA + " Use small stub classes for redis and the qdrant reader; respx for ollama.", deps=["T-api-012"])
u(24, "F-status", "model catalog", "services/models_catalog.py", "integration/test_models_catalog.py", ["get_catalog"], [
  "ollama tags ['bge-m3:latest', 'qwen3:8b'] → ollama_reachable True, dense installed: bge-m3 True, others False; order bge-m3, nomic-embed-text, mxbai-embed-large, all-minilm with dims 1024, 768, 1024, 384 and max_tokens 8192, 8192, 512, 256",
  "tag 'all-minilm' (no suffix) counts as installed",
  "'bge-m3x:latest' does not count as bge-m3",
  "ollama down → reachable False, installed [] and every installed False",
  "sparse == ['Qdrant/bm25', 'prithivida/Splade_PP_en_v1'] and rerank == catalog.RERANK_MODELS",
], intro=INFRA + " respx for ollama.", deps=["T-api-012"])
u(25, "F-pipeline-graph", "pipeline graph store", "services/pipeline_graphs.py", "integration/test_pipeline_graphs_service.py", ["put_graph", "list_graphs", "get_graph"], [
  "put_graph('chunk', 'fixed', fixture graph) then get_graph → same dict",
  "put twice → second replaces the first (one row)",
  "body stage mismatch → VALIDATION_ERROR details {'field': 'stage'}; variant mismatch → field 'variant'",
  "list_graphs order: put generate/default, chunk/semantic, chunk/fixed, parse/plain_text → parse/plain_text, chunk/fixed, chunk/semantic, generate/default",
  "get_graph unknown → PIPELINE_GRAPH_NOT_FOUND details {'stage', 'variant'}",
], intro=INFRA + " Graph fixture: tests.conftest.FIXTURES / 'shared__pipeline-graph.json' (stage chunk, variant fixed); copy and change stage/variant for others.")
u(26, "F-one-command", "bootstrap migrations + seed", "services/bootstrap.py", "integration/test_bootstrap_seed.py", ["run_migrations", "seed"], [
  "seed on an empty DB → buckets 'uploads' and 'artifacts' in store.buckets, settings row 'app' with ollama.url == settings.ollama_url_default and chat_model 'qwen3:8b', exactly one collection named 'default' (bge-m3, Qdrant/bm25, 1024)",
  "seed twice → still one settings row and one collection; existing settings values are not overwritten",
  "seed when another collection already exists → no 'default' created",
  "run_migrations(DATABASE_URL of a fresh database 'ragfun_mig_<hex>' created with CREATE DATABASE) creates all 8 tables (query information_schema.tables); running it twice is a no-op",
], intro=INFRA + " For run_migrations create a throwaway database via an AUTOCOMMIT connection on the postgres-test server and drop it afterwards.", deps=["T-api-003", "T-api-011"], e2e=["tests/e2e/test_bootstrap.py"])
