---
id: T-web-015t
kind: test
feature: F-status
title: 'Write tests: StatusBar'
service: web
depends_on:
- T-web-004
edit:
- services/web/tests/components/StatusBar.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/components/StatusBar.test.tsx && npx eslint tests/components/StatusBar.test.tsx && npx vitest list tests/components/StatusBar.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/components/StatusBar.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: StatusBar. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-015 implements it.

## Context
Stub `services/web/src/components/StatusBar.tsx` (signature and props are final):
```tsx
/**
 * Polls getStatus every 5 s (react-query refetchInterval). Renders one pill per component in response
 * order: text = component name, data-ok="true|false", green when ok, red when not with title = detail.
 * While loading: "Checking services…". Request error: one red pill "api" with the error message.
 */
export function StatusBar(): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. while loading → 'Checking services…'
2. 8 components → 8 elements with data-ok; red one has title = detail
3. GET /status 500 → one pill 'api' with data-ok false
4. refetchInterval: uses react-query with refetchInterval 5000 (fake timers: advance 5 s → 2 requests)

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
