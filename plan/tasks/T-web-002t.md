---
id: T-web-002t
kind: test
feature: F-stage-flow
title: 'Write tests: api wrappers runs.ts'
service: web
depends_on: []
edit:
- services/web/tests/api/runs.test.ts
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/api/runs.test.ts && npx eslint tests/api/runs.test.ts && npx vitest list tests/api/runs.test.ts'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/api/runs.test.ts
max_attempts: 3
---

## Goal
Write unit tests for: api wrappers runs.ts. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-002 implements it.

## Context
Implement with `apiFetch` from src/api/client.ts (it prefixes /api/v1, sends JSON, throws ApiError). Paths and bodies: contracts/openapi/api.yaml.

Stub `services/web/src/api/runs.ts` (signature and props are final):
```tsx
import type {
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
export function startIngestStage(
  _runId: string,
  _stage: IngestStage,
  _params: object,
): Promise<StageRun> {
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
export function startQueryStage(
  _runId: string,
  _stage: QueryStage,
  _params: object,
): Promise<StageRun> {
  throw new Error('not implemented')
}

/** POST /query-runs/{runId}/run-all { from_stage, params } → QueryRun (200 or 202). */
export function runAllQuery(
  _runId: string,
  _fromStage: QueryStage | null,
  _params: { transform: object; retrieve: object; rerank: object; generate: object },
): Promise<QueryRun> {
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
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. createIngestRun(f, c) → POST /api/v1/ingest-runs { file_id: f, collection_id: c }
2. startIngestStage(r, 'chunk', p) → POST /api/v1/ingest-runs/r/stages/chunk { params: p }
3. runAllIngest(r, null, params) → POST /ingest-runs/r/run-all { from_stage: null, params }
4. createQueryRun(c, 'q?') → POST /query-runs { collection_id: c, question: 'q?' }; startQueryStage(r, 'retrieve', p) → /query-runs/r/stages/retrieve
5. runAllQuery(r, null, params) → POST /query-runs/r/run-all { from_stage: null, params }
6. listStageRuns(r, 'parse') → GET /stage-runs?run_id=r&stage=parse
7. getArtifact(id) → GET /stage-runs/{id}/artifact returns the JSON; pageImageUrl('s', 2) == '/api/v1/stage-runs/s/pages/2'
8. 409 STAGE_PREREQUISITE_MISSING → ApiError with details.missing

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
