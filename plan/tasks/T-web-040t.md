---
id: T-web-040t
kind: test
feature: F-qdrant-browser
title: 'Write tests: QdrantBrowserPage'
service: web
depends_on:
- T-web-003
edit:
- services/web/tests/pages/QdrantBrowserPage.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/pages/QdrantBrowserPage.test.tsx && npx eslint tests/pages/QdrantBrowserPage.test.tsx && npx vitest list tests/pages/QdrantBrowserPage.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/pages/QdrantBrowserPage.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: QdrantBrowserPage. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-040 implements it.

## Context
Stub `services/web/src/pages/QdrantBrowserPage.tsx` (signature and props are final):
```tsx
/**
 * Route "/qdrant/:collectionId?". Collection select (navigates). Info card from getQdrantInfo: exists,
 * status, points_count, vector config (shows the names text-dense / text-sparse, size, distance,
 * modifier), payload indexes table. <FilterBuilder> + matching count (countPoints). Points table
 * (scrollPoints limit 20, "Load more" with next_offset): point id (first 8), filename, page,
 * element_type, tags, content (80 chars). Click row → side panel with getPoint raw JSON (<pre>) showing
 * the first 16 dense dims + "… (<n> more)". exists false → "Nothing stored yet in this collection — run
 * the Store stage of an ingest run."
 */
export function QdrantBrowserPage(): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. info card: status 'green', '4 points', payload index table rows
2. points table first row: id first 8 chars, filename, page, element_type
3. 'Load more' appears when next_offset is set and sends it as offset
4. row click → side panel with first 16 dims and '… (368 more)'
5. collection select change navigates to /qdrant/<id>

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
