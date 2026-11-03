---
id: T-web-016t
kind: test
feature: F-upload
title: 'Write tests: UploadDropzone'
service: web
depends_on:
- T-web-001
- T-web-008
edit:
- services/web/tests/components/UploadDropzone.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/components/UploadDropzone.test.tsx && npx eslint tests/components/UploadDropzone.test.tsx && npx vitest list tests/components/UploadDropzone.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/components/UploadDropzone.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: UploadDropzone. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-016 implements it.

## Context
Stub `services/web/src/components/UploadDropzone.tsx` (signature and props are final):
```tsx
export interface UploadDropzoneProps {
  onUploaded: (batchId: string) => void
}

/**
 * Drop zone + hidden <input type="file" multiple aria-label="Choose files">. Selected files listed by
 * name. Optional batch name input (label "Batch name") and <TagEditor> for batch tags. Button
 * "Upload N files" (disabled with 0 files) → uploadBatch → onUploaded(batch.id), clear selection.
 * ApiError (e.g. UNSUPPORTED_FILE_TYPE) → <ErrorBox>, selection kept.
 */
export function UploadDropzone(_props: UploadDropzoneProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. choose 2 files via 'Choose files' → both names listed; button 'Upload 2 files' enabled; with 0 files button disabled
2. batch name + tag 'hr' → POST multipart has name and tags 'hr'; onUploaded(batch id); selection cleared
3. 415 response → alert with 'UNSUPPORTED_FILE_TYPE', file names still listed

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
