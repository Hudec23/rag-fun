---
id: T-web-042t
kind: test
feature: F-pipeline-graph
title: 'Write tests: PipelinesPage'
service: web
depends_on:
- T-web-004
edit:
- services/web/tests/pages/PipelinesPage.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/pages/PipelinesPage.test.tsx && npx eslint tests/pages/PipelinesPage.test.tsx && npx vitest list tests/pages/PipelinesPage.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/pages/PipelinesPage.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: PipelinesPage. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-042 implements it.

## Context
Stub `services/web/src/pages/PipelinesPage.tsx` (signature and props are final):
```tsx
/**
 * Route "/pipelines". listPipelineGraphs → left list grouped by stage ("chunk / semantic"), selected
 * graph rendered with <PipelineGraph>. Empty → "No pipeline graphs reported yet — is the worker
 * running?"
 */
export function PipelinesPage(): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. graphs grouped as 'chunk / fixed' entries; first graph selected by default
2. clicking another entry renders its PipelineGraph (vi.mock PipelineGraph to print variant)
3. empty → 'No pipeline graphs reported yet — is the worker running?'

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
