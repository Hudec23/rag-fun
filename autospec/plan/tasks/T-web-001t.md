---
id: T-web-001t
kind: test
feature: F-upload
title: 'Write tests: api wrappers batches.ts + files.ts'
service: web
depends_on: []
edit:
- services/web/tests/api/batchesFiles.test.ts
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/api/batchesFiles.test.ts && npx eslint tests/api/batchesFiles.test.ts && npx vitest list tests/api/batchesFiles.test.ts'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/api/batchesFiles.test.ts
max_attempts: 3
---

## Goal
Write unit tests for: api wrappers batches.ts + files.ts. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-001 implements it.

## Context
Implement with `apiFetch` from src/api/client.ts (it prefixes /api/v1, sends JSON, throws ApiError). Paths and bodies: contracts/openapi/api.yaml.

Stub `services/web/src/api/batches.ts` (signature and props are final):
```tsx
import type { BatchList, BatchWithFiles, Batch, IngestParamsAll, IngestRun } from './types'

/** POST /batches multipart: one 'files' part per file, 'name' only when given, 'tags' = tags.join(',')
 * only when tags non-empty. → 201 BatchWithFiles. */
export function uploadBatch(
  _files: File[],
  _name: string | null,
  _tags: string[],
): Promise<BatchWithFiles> {
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
export function updateBatch(
  _id: string,
  _patch: { name?: string; tags?: string[] },
): Promise<Batch> {
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
```

Stub `services/web/src/api/files.ts` (signature and props are final):
```tsx
import type { FileItem, FileList } from './types'
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
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. uploadBatch([fileA, fileB], 'n', ['x', 'y']) → POST /api/v1/batches multipart: formData.getAll('files') has 2 entries, name 'n', tags 'x,y'; resolves the 201 body
2. uploadBatch(files, null, []) sends no 'name' and no 'tags' fields
3. listBatches(10, 20) → GET /api/v1/batches?limit=10&offset=20
4. updateBatch(id, { tags: ['a'] }) → PATCH body exactly { tags: ['a'] }
5. ingestBatch(id, collectionId, INGEST_DEFAULTS) → POST /batches/{id}/ingest body { collection_id, params }
6. listFiles({ batch_id: 'b', tag: undefined }) → query has batch_id=b and no tag param
7. updateFileTags(id, ['t']) → PATCH /files/{id} { tags: ['t'] }; deleteFile resolves undefined on 204
8. a 415 error body → promise rejects with ApiError code UNSUPPORTED_FILE_TYPE and status 415

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
