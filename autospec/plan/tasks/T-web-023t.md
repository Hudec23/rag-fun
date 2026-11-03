---
id: T-web-023t
kind: test
feature: F-embed
title: 'Write tests: SimilarityMatrix'
service: web
depends_on: []
edit:
- services/web/tests/viz/SimilarityMatrix.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/viz/SimilarityMatrix.test.tsx && npx eslint tests/viz/SimilarityMatrix.test.tsx && npx vitest list tests/viz/SimilarityMatrix.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/SimilarityMatrix.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: SimilarityMatrix. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-023 implements it.

## Context
Stub `services/web/src/viz/SimilarityMatrix.tsx` (signature and props are final):
```tsx
export interface SimilarityMatrixProps {
  matrix: number[][]
  labels: string[]
}

/**
 * Plotly heatmap, z = matrix, x = y = labels, zmin -1, zmax 1, colorscale 'Viridis', title
 * "Cosine similarity". Below: the 5 most similar off-diagonal pairs (i<j) as "<label i> ↔ <label j>:
 * <value to 3 decimals>", sorted desc. Empty → "No vectors".
 */
export function SimilarityMatrix(_props: SimilarityMatrixProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. EMBED.similarity 4x4 → heatmap z == matrix, zmin -1, zmax 1
2. top pairs: 6 off-diagonal pairs for 4 labels, shows 5 lines with '↔', first is the max similarity (3 decimals)
3. empty matrix → 'No vectors'

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
