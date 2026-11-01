---
id: T-web-006t
kind: test
feature: F-live-progress
title: 'Write tests: useIngestRun + useQueryRun live hooks'
service: web
depends_on:
- T-web-002
edit:
- services/web/tests/hooks/useRun.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/hooks/useRun.test.tsx && npx eslint tests/hooks/useRun.test.tsx && npx vitest list tests/hooks/useRun.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/hooks/useRun.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: useIngestRun + useQueryRun live hooks. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-006 implements it.

## Context
renderHook wrapped in a QueryClientProvider (create the wrapper in the test).

Stub `services/web/src/hooks/useRun.ts` (signature and props are final):
```tsx
import type { IngestRun, QueryRun } from '../api/types'

export interface LiveRun<T> {
  run: T | undefined
  error: unknown
  /** latest stage.progress per stage_run_id */
  progress: Record<string, { done: number; total: number; message: string }>
  /** generate.token texts joined in index order per stage_run_id */
  tokens: Record<string, string>
}

/** react-query ['ingest-run', runId] via getIngestRun + useRunEvents: run.updated, stage.started,
 * stage.completed, stage.failed → invalidate the query; stage.progress → progress map. */
export function useIngestRun(_runId: string): LiveRun<IngestRun> {
  throw new Error('not implemented')
}

/** Same for query runs (['query-run', runId], getQueryRun); generate.token → tokens map. */
export function useQueryRun(_runId: string): LiveRun<QueryRun> {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. useIngestRun(RUN_ID) fetches GET /api/v1/ingest-runs/RUN_ID and exposes run
2. stage.completed event → the run is refetched (msw handler called twice)
3. stage.progress {stage_run_id 's', done 1, total 3, message 'm'} → progress['s'] == { done: 1, total: 3, message: 'm' }
4. useQueryRun: generate.token index 0 'Hel', index 1 'lo' → tokens[stage_run_id] == 'Hello'; tokens arriving out of order (1 then 0) still join in index order
5. run.updated → refetch

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
