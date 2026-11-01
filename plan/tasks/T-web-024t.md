---
id: T-web-024t
kind: test
feature: F-retrieve
title: 'Write tests: HybridLists'
service: web
depends_on: []
edit:
- services/web/tests/viz/HybridLists.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/viz/HybridLists.test.tsx && npx eslint tests/viz/HybridLists.test.tsx && npx vitest list tests/viz/HybridLists.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/HybridLists.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: HybridLists. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-024 implements it.

## Context
Stub `services/web/src/viz/HybridLists.tsx` (signature and props are final):
```tsx
import type { RetrieveArtifact } from '../api/types'

export interface HybridListsProps {
  artifact: RetrieveArtifact
}

/**
 * Three columns for per_query[0] (with a query selector when per_query.length > 1): "Dense", "Sparse"
 * (column omitted when the list is null), "Fused (RRF)" from artifact.fused. Each row: rank, score (4
 * decimals), first 120 chars, filename + page. Hovering/clicking a row highlights the same doc_id in all
 * columns (data-highlighted="true"). Fused rows show source ranks as "D#2 S#5".
 */
export function HybridLists(_props: HybridListsProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. RETRIEVE → columns 'Dense', 'Sparse', 'Fused (RRF)'; fused first row shows 'D#1 S#2'
2. dense null → no 'Dense' column
3. click a dense row → every row with the same doc_id has data-highlighted 'true'
4. per_query length 2 → a query selector; switching shows the second query's lists

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
