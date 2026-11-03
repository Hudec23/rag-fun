---
id: T-web-025t
kind: test
feature: F-rerank
title: 'Write tests: RerankDiff'
service: web
depends_on: []
edit:
- services/web/tests/viz/RerankDiff.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/viz/RerankDiff.test.tsx && npx eslint tests/viz/RerankDiff.test.tsx && npx vitest list tests/viz/RerankDiff.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/RerankDiff.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: RerankDiff. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-025 implements it.

## Context
Stub `services/web/src/viz/RerankDiff.tsx` (signature and props are final):
```tsx
import type { RerankArtifact } from '../api/types'

export interface RerankDiffProps {
  artifact: RerankArtifact
}

/**
 * Two columns "Before" (artifact.before) and "After" (artifact.after[].hit). After rows show
 * "↑3" (green) / "↓2" (red) / "=" from previous_rank − new rank, plus rerank_score (4 decimals) or "—".
 * disabled → banner "Reranking disabled — showing retrieval order".
 */
export function RerankDiff(_props: RerankDiffProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. RERANK → after row 1 shows '↑1' (previous 2 → 1), row 2 '↓1', row 3 '↑1'
2. rerank_score 0.97 shown as '0.9700'; null → '—'
3. enabled false → 'Reranking disabled — showing retrieval order'

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
