# Contracts (frozen)

Every interface that crosses a service boundary. **The executor reads these and never changes them.**
Validate after any planner change:

```sh
docker run --rm -v "$PWD":/w -w /w python:3.12.16-slim sh -c \
  'pip install -q --root-user-action=ignore --disable-pip-version-check jsonschema==4.26.0 \
   openapi-spec-validator==0.9.0 pyyaml==6.0.3 && python scripts/validate-contracts.py'
```

| File | Arrow (SYSTEM.md §3) | Producer → Consumer |
|---|---|---|
| `openapi/api.yaml` | web → api (REST), web ← api (SSE) | api → web |
| `openapi/internal.yaml` | worker → api (callbacks) | worker → api |
| `jobs/{parse,chunk,embed,store}.schema.json` | api → worker, queue `ingest` | api → worker |
| `jobs/{transform,retrieve,rerank,generate}.schema.json` | api → worker, queue `query` | api → worker |
| `jobs/{drop_collection,delete_points}.schema.json` | api → worker, queue `query` | api → worker |
| `events/stage.*.schema.json`, `events/generate.token.schema.json` | worker → api → web (pub/sub → SSE) | worker → api, web |
| `events/run.updated.schema.json` | api → web (pub/sub → SSE) | api → web |
| `events/worker.heartbeat.schema.json` | worker → api (Redis key) | worker → api |
| `artifacts/*.schema.json` | worker → S3 → api → web | worker → worker, api, web |
| `qdrant/payload.schema.json` | worker → Qdrant ← api | worker → worker, api |
| `shared/common.schema.json` | reusable types (IDs, params, filters, Hit, Error) | – |
| `shared/summary.schema.json` | stage summaries (callback, event, StageRun) | worker → api, web |
| `shared/pipeline-graph.schema.json` | worker → api → web | worker → api, web |
| `shared/errors.json` | error codes + HTTP status | all |

## Generated code (planner runs generators in the walking skeleton; output committed; executor never regenerates)

| Output | Generator | Input |
|---|---|---|
| `services/web/src/api/schema.d.ts` | openapi-typescript 7.13.0 | `contracts/openapi/api.yaml` |
| `services/api/src/rag_api/contracts_gen/*.py` | datamodel-code-generator 0.87.0 (pydantic v2, `--output-model-type pydantic_v2.BaseModel --use-annotated --field-constraints --extra-fields forbid`) | jobs, events, artifacts, shared, qdrant schemas |
| `services/worker/src/rag_worker/contracts_gen/*.py` | same | same |

api request/response models for `openapi/api.yaml` + `internal.yaml` are written by hand in
`rag_api/schemas/` (FastAPI needs them as route types) and checked against the contract by the provider tests below.

## Contract test plan

Every row becomes locked tests in step 3. Provider = side that produces the message/serves the endpoint,
consumer = side that reads it. Shared fixtures: `tests/contract_fixtures/` (example JSON per schema,
written by the planner, valid against the schema; copied into each service's tests by the skeleton).

| Contract | Provider test (where) | Consumer test (where) |
|---|---|---|
| openapi/api.yaml | api `tests/integration/test_contract_api.py`: for every operation, call with the contract example request and validate the response body against the response schema (jsonschema over the bundled spec); error responses for each listed status | web `tests/api/*.test.ts`: msw handlers return the contract examples; fetch wrappers parse them and types compile against `schema.d.ts` |
| openapi/internal.yaml | api `tests/integration/test_contract_internal.py`: examples accepted (204), wrong token 401, unknown id 404, duplicate result ignored | worker `tests/unit/test_report.py`: respx captures the callback bodies; validate against `StageResult` / `StageStarted`; retry schedule 1,2,4,8,16 s on 5xx, no retry on 4xx |
| jobs/*.schema.json | api `tests/unit/test_job_payloads.py`: payload built for each stage validates against its job schema | worker `tests/unit/test_job_models.py`: every job example parses into the generated model; unknown field rejected |
| events/stage.*, generate.token | worker `tests/unit/test_events.py`: published messages validate against schemas; completed published after callback | api `tests/integration/test_sse_relay.py`: message published on Redis appears unchanged on SSE with correct `event:` name; web `tests/hooks/useRunEvents.test.ts` parses examples |
| events/run.updated | api `tests/integration/test_run_updated.py` | web `tests/hooks/useRunEvents.test.ts` |
| events/worker.heartbeat | worker `tests/unit/test_heartbeat.py`: key, TTL 30, JSON valid | api `tests/integration/test_status.py`: key present → ok, absent → not ok |
| artifacts/*.schema.json | worker `tests/unit/test_<stage>_artifact.py` (fake models): artifact for fixture files validates | api `tests/integration/test_artifact_proxy.py` returns stored JSON unchanged; web view tests render the fixture artifacts |
| qdrant/payload.schema.json | worker `tests/integration/test_store_qdrant.py` (qdrant-test): stored payload validates, vector names, point id = convert_id(doc_id), indexes exist | api `tests/integration/test_qdrant_browser.py`: scroll/point/facet over points seeded with the fixture payload |
| shared/summary.schema.json | worker (inside artifact tests) | api (inside internal contract test) |
| shared/pipeline-graph.schema.json | worker `tests/unit/test_pipeline_graphs.py`: every (stage, variant) graph validates; secrets masked | api `tests/integration/test_pipeline_graphs.py`; web `tests/pages/PipelineGraph.test.tsx` |
| shared/errors.json | api `tests/unit/test_errors.py`: every code maps to its HTTP status; handler emits Error shape | web `tests/components/ErrorBox.test.tsx` shows code + message |
