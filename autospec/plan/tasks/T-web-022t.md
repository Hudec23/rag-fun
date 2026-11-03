---
id: T-web-022t
kind: test
feature: F-embed
title: 'Write tests: ScatterPlot'
service: web
depends_on: []
edit:
- services/web/tests/viz/ScatterPlot.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/viz/ScatterPlot.test.tsx && npx eslint tests/viz/ScatterPlot.test.tsx && npx vitest list tests/viz/ScatterPlot.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/ScatterPlot.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: ScatterPlot. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-022 implements it.

## Context
Stub `services/web/src/viz/ScatterPlot.tsx` (signature and props are final):
```tsx
export interface ScatterPlotProps {
  points2d: number[][] | null
  points3d: number[][] | null
  labels: string[]
  groups: string[]
  method: 'pca' | 'umap'
}

/**
 * Toggle buttons "2D" / "3D" (default 2D). 2D → Plotly 'scatter' mode markers; 3D → 'scatter3d'.
 * One trace per distinct group (legend), hover text = labels[i]. Selected dimension's points null →
 * message "Not enough chunks for <METHOD> <2D|3D>". Title "<PCA|UMAP> projection".
 */
export function ScatterPlot(_props: ScatterPlotProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. points2d for 4 points, groups ['a','a','b','b'] → 2 traces type 'scatter' named a and b
2. click '3D' → traces type 'scatter3d'
3. method umap and points2d null → 'Not enough chunks for UMAP 2D'
4. hover text equals labels

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
