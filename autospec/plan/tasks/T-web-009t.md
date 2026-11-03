---
id: T-web-009t
kind: test
feature: F-stage-flow
title: 'Write tests: ProgressBar'
service: web
depends_on: []
edit:
- services/web/tests/components/ProgressBar.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/components/ProgressBar.test.tsx && npx eslint tests/components/ProgressBar.test.tsx && npx vitest list tests/components/ProgressBar.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/components/ProgressBar.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: ProgressBar. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-009 implements it.

## Context
Stub `services/web/src/components/ProgressBar.tsx` (signature and props are final):
```tsx
export interface ProgressBarProps {
  done: number
  total: number
  message?: string
}

/**
 * role="progressbar" with aria-valuenow=done, aria-valuemax=total, width % = round(done/total*100)
 * (0 when total ≤ 0, max 100). Shows "<done>/<total>" and message when given.
 */
export function ProgressBar(_props: ProgressBarProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. done 1 total 4 → role progressbar aria-valuenow 1 aria-valuemax 4, text '1/4', inner width style '25%'
2. total 0 → width '0%'
3. done 9 total 4 → width '100%'
4. message shown when given

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
