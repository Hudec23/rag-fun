---
id: T-web-035t
kind: test
feature: F-rerank
title: 'Write tests: RerankView'
service: web
depends_on:
- T-web-025
edit:
- services/web/tests/stages/RerankView.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/stages/RerankView.test.tsx && npx eslint tests/stages/RerankView.test.tsx && npx vitest list tests/stages/RerankView.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/stages/RerankView.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: RerankView. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-035 implements it.

## Context
Fixtures from tests/setup/fixtures.ts; derive variants with spread, e.g. { ...CHUNK, strategy: 'semantic', semantic: {...} }.

Stub `services/web/src/components/stages/RerankView.tsx` (signature and props are final):
```tsx
import type { RerankArtifact } from '../../api/types'

export interface RerankViewProps {
  stageRunId: string
  artifact: RerankArtifact
}

/**
 * Header "<model> · top <top_n>" (or disabled banner via RerankDiff) then <RerankDiff>.
 */
export function RerankView(_props: RerankViewProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. header 'Xenova/ms-marco-MiniLM-L-6-v2 · top 3'
2. renders RerankDiff rows
3. disabled artifact shows the disabled banner

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
