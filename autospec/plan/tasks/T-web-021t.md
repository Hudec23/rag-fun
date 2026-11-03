---
id: T-web-021t
kind: test
feature: F-embed
title: 'Write tests: VectorHeatmap'
service: web
depends_on: []
edit:
- services/web/tests/viz/VectorHeatmap.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/viz/VectorHeatmap.test.tsx && npx eslint tests/viz/VectorHeatmap.test.tsx && npx vitest list tests/viz/VectorHeatmap.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/VectorHeatmap.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: VectorHeatmap. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-021 implements it.

## Context
Stub `services/web/src/viz/VectorHeatmap.tsx` (signature and props are final):
```tsx
export interface VectorHeatmapProps {
  vectors: number[][]
  labels: string[]
}

/**
 * Plotly heatmap: z = vectors (rows = chunks, labels on y), x = dimension index, colorscale 'RdBu',
 * zmid 0, layout title "Dense vectors (<n> × <dims>)". Empty → "No vectors".
 */
export function VectorHeatmap(_props: VectorHeatmapProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. 2 vectors of 3 dims → plot data[0].type 'heatmap', z equals vectors, y labels, colorscale 'RdBu', zmid 0
2. title contains '2 × 3'
3. empty → 'No vectors'

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
