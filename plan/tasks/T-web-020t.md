---
id: T-web-020t
kind: test
feature: F-embed
title: 'Write tests: TokenView'
service: web
depends_on: []
edit:
- services/web/tests/viz/TokenView.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/viz/TokenView.test.tsx && npx eslint tests/viz/TokenView.test.tsx && npx vitest list tests/viz/TokenView.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/TokenView.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: TokenView. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-020 implements it.

## Context
Stub `services/web/src/viz/TokenView.tsx` (signature and props are final):
```tsx
export interface TokenViewProps {
  tokens: string[]
  tokenCount: number
  maxTokens: number
  overLimit: boolean
}

/**
 * Token pills in order (alternating two background colors, data-testid="token"), header
 * "<tokenCount> / <maxTokens> tokens", red badge "over limit — truncated by the model" when overLimit,
 * note "showing first <tokens.length>" when tokens.length < tokenCount.
 */
export function TokenView(_props: TokenViewProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. tokens ['[CLS]', 'hi', '[SEP]'] tokenCount 3 max 256 → 3 [data-testid=token], header '3 / 256 tokens'
2. overLimit → 'over limit — truncated by the model'
3. tokens.length 2 < tokenCount 5000 → 'showing first 2'

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
