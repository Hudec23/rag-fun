---
id: T-web-005t
kind: test
feature: F-live-progress
title: 'Write tests: useRunEvents hook'
service: web
depends_on: []
edit:
- services/web/tests/hooks/useRunEvents.test.ts
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/hooks/useRunEvents.test.ts && npx eslint tests/hooks/useRunEvents.test.ts && npx vitest list tests/hooks/useRunEvents.test.ts'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/hooks/useRunEvents.test.ts
max_attempts: 3
---

## Goal
Write unit tests for: useRunEvents hook. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-005 implements it.

## Context
Use renderHook from @testing-library/react. EventSource is globally replaced by MockEventSource (tests/setup/eventsource.ts).

Stub `services/web/src/hooks/useRunEvents.ts` (signature and props are final):
```tsx
import type { RunEvent } from '../api/types'

/** Opens EventSource(`${API_BASE}/events?run_id=${runId}`) while runId is non-null; for each of the
 * 6 event types (addEventListener per type) parses event.data as JSON and calls onEvent.
 * Closes on unmount or runId change. Malformed JSON is ignored. */
export function useRunEvents(_runId: string | null, _onEvent: (e: RunEvent) => void): void {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. renderHook(() => useRunEvents('r1', fn)) → one MockEventSource with url '/api/v1/events?run_id=r1'
2. emit('stage.progress', {...}) → fn called once with the parsed object
3. each of the 6 types (stage.started, stage.progress, stage.completed, stage.failed, generate.token, run.updated) is delivered
4. malformed JSON data is ignored (fn not called, no throw)
5. unmount → source.closed true; runId null → no EventSource created
6. rerender with another runId closes the old source and opens a new one

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
