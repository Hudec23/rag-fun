---
id: T-web-043t
kind: test
feature: F-generate
title: 'Write tests: QueryPage'
service: web
depends_on:
- T-web-002
edit:
- services/web/tests/pages/QueryPage.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/pages/QueryPage.test.tsx && npx eslint tests/pages/QueryPage.test.tsx && npx vitest list tests/pages/QueryPage.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/pages/QueryPage.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: QueryPage. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-043 implements it.

## Context
Stub `services/web/src/pages/QueryPage.tsx` (signature and props are final):
```tsx
/**
 * Route "/query" (new) and "/query/:runId". New: collection select + question textarea + "Ask" (disabled
 * while the question is empty) → createQueryRun → navigate to /query/<id>. With runId: useQueryRun;
 * header with the question and "Run all" → runAllQuery(runId, null, {transform, retrieve, rerank,
 * generate} = each stage's current params or lib/defaults); <StageStepper> transform/retrieve/rerank/
 * generate + selected <StagePanel> (generate gets liveText = live.tokens[generate stage run id]).
 */
export function QueryPage(): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. /query: collection select + question + 'Ask' → POST /query-runs then navigates to /query/<id>
2. 'Ask' disabled for an empty question
3. /query/:runId → question header, stepper transform/retrieve/rerank/generate, 'Run all' → POST /query-runs/<id>/run-all { from_stage: null, params } with TRANSFORM/RETRIEVE/RERANK/GENERATE defaults
4. generate panel receives liveText from generate.token events (vi.mock StagePanel to print liveText)

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
