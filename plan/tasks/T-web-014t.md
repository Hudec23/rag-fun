---
id: T-web-014t
kind: test
feature: F-collections
title: 'Write tests: CreateCollectionForm'
service: web
depends_on:
- T-web-004
edit:
- services/web/tests/components/CreateCollectionForm.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/components/CreateCollectionForm.test.tsx && npx eslint tests/components/CreateCollectionForm.test.tsx && npx vitest list tests/components/CreateCollectionForm.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/components/CreateCollectionForm.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: CreateCollectionForm. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-014 implements it.

## Context
Stub `services/web/src/components/CreateCollectionForm.tsx` (signature and props are final):
```tsx
export interface CreateCollectionFormProps {
  onCreated?: () => void
}

/**
 * Inline form: name input (label "Name"), dense model select (label "Dense model", 4 options from
 * DenseModel), sparse model select (label "Sparse model"), button "Create". Submit → createCollection;
 * success → invalidate ['collections'], clear name, onCreated(); ApiError → <ErrorBox>. Button disabled
 * while name is empty or the request is pending.
 */
export function CreateCollectionForm(_props: CreateCollectionFormProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. 'Create' disabled while Name is empty
2. fill name 'exp', choose dense 'all-minilm' → POST body { name: 'exp', dense_model: 'all-minilm', sparse_model: 'Qdrant/bm25' }; afterwards name input empty and onCreated called
3. 409 → alert 'COLLECTION_NAME_TAKEN: …'
4. Dense model select has exactly the 4 models; Sparse model the 2

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
