---
id: T-web-039t
kind: test
feature: F-stage-flow
title: 'Write tests: IngestRunPage'
service: web
depends_on:
- T-web-002
edit:
- services/web/tests/pages/IngestRunPage.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/pages/IngestRunPage.test.tsx && npx eslint tests/pages/IngestRunPage.test.tsx && npx vitest list tests/pages/IngestRunPage.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/pages/IngestRunPage.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: IngestRunPage. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-039 implements it.

## Context
Stub `services/web/src/pages/IngestRunPage.tsx` (signature and props are final):
```tsx
/**
 * Route "/ingest/:runId". useIngestRun(runId). Header: filename, collection, "Run all" button
 * (runAllIngest(runId, null, current params of each stage or INGEST_DEFAULTS)) and pending plan chips.
 * <StageStepper> for parse/chunk/embed/store and the selected <StagePanel>. Default selection = first
 * stage not done (else store), computed ONCE when the run first loads; afterwards only the user changes
 * it. The panel gets run = run.stages[stage] and progress = live.progress[that stage run's id]. Passes
 * extra.chunks (from the active chunk artifact) to the embed panel and extra.collectionId to store.
 * Loading/error states as in CollectionsPage.
 */
export function IngestRunPage(): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. header shows filename and 'Run all'; stepper with 4 stages; default selection = first stage not done
2. 'Run all' → POST /ingest-runs/r/run-all { from_stage: null, params } where params uses each stage's current params or INGEST_DEFAULTS
3. pending plan chips for run_all_pending ['embed', 'store']
4. selecting 'embed' shows its StagePanel (vi.mock StagePanel to print the stage)

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
