---
id: T-web-038t
kind: test
feature: F-upload
title: 'Write tests: FilesPage'
service: web
depends_on:
- T-web-001
edit:
- services/web/tests/pages/FilesPage.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/pages/FilesPage.test.tsx && npx eslint tests/pages/FilesPage.test.tsx && npx vitest list tests/pages/FilesPage.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/pages/FilesPage.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: FilesPage. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-038 implements it.

## Context
Stub `services/web/src/pages/FilesPage.tsx` (signature and props are final):
```tsx
/**
 * Route "/". <UploadDropzone> on top; then batches (listBatches) each with its files table: filename,
 * type, size (KB/MB, 1 decimal), tags (<TagEditor> → updateFileTags), actions "Ingest…" (collection
 * select + "Start" → createIngestRun then navigate to /ingest/<runId>) and "Delete" (confirm →
 * deleteFile). Batch row: name, tags editor (updateBatch), "Ingest batch" (collection select → ingestBatch
 * with INGEST_DEFAULTS, then shows "<n> runs started" with links).
 */
export function FilesPage(): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. batches listed with file rows: filename, type, size '470.8 KB' for 482113 bytes
2. 'Ingest…' on a file → collection select + 'Start' → POST /ingest-runs then navigates to /ingest/<id> (assert via a route element in renderWithProviders)
3. 'Delete' with window.confirm mocked true → DELETE /files/{id}
4. 'Ingest batch' → POST /batches/{id}/ingest with INGEST_DEFAULTS and shows '<n> runs started'

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
