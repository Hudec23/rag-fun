---
id: T-web-034t
kind: test
feature: F-retrieve
title: 'Write tests: RetrieveView'
service: web
depends_on:
- T-web-024
edit:
- services/web/tests/stages/RetrieveView.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/stages/RetrieveView.test.tsx && npx eslint tests/stages/RetrieveView.test.tsx && npx vitest list tests/stages/RetrieveView.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/stages/RetrieveView.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: RetrieveView. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-034 implements it.

## Context
Fixtures from tests/setup/fixtures.ts; derive variants with spread, e.g. { ...CHUNK, strategy: 'semantic', semantic: {...} }.

Stub `services/web/src/components/stages/RetrieveView.tsx` (signature and props are final):
```tsx
import type { RetrieveArtifact } from '../../api/types'

export interface RetrieveViewProps {
  stageRunId: string
  artifact: RetrieveArtifact
}

/**
 * Header "<mode> · top_k <k> · RRF k <rrf_k>" and active filters as chips ("tags in finance");
 * then <HybridLists>.
 */
export function RetrieveView(_props: RetrieveViewProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. header 'hybrid · top_k 10 · RRF k 60'
2. filter chip 'tags in finance'
3. renders HybridLists

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
