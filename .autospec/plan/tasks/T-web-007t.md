---
id: T-web-007t
kind: test
feature: F-stage-flow
title: 'Write tests: useArtifact hook'
service: web
depends_on:
- T-web-002
edit:
- services/web/tests/hooks/useArtifact.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/hooks/useArtifact.test.tsx && npx eslint tests/hooks/useArtifact.test.tsx && npx vitest list tests/hooks/useArtifact.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/hooks/useArtifact.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: useArtifact hook. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-007 implements it.

## Context
Stub `services/web/src/hooks/useArtifact.ts` (signature and props are final):
```tsx
/** react-query ['artifact', stageRunId] via getArtifact<T>; disabled when stageRunId is null;
 * staleTime Infinity (artifacts never change). */
export function useArtifact<T>(_stageRunId: string | null): {
  data: T | undefined
  error: unknown
  isLoading: boolean
} {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. useArtifact('s1') fetches /api/v1/stage-runs/s1/artifact and returns data
2. useArtifact(null) makes no request and isLoading false
3. 404 ARTIFACT_NOT_FOUND → error is ApiError

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
