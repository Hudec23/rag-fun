---
id: T-web-026t
kind: test
feature: F-generate
title: 'Write tests: TokenBudgetBar'
service: web
depends_on: []
edit:
- services/web/tests/viz/TokenBudgetBar.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/viz/TokenBudgetBar.test.tsx && npx eslint tests/viz/TokenBudgetBar.test.tsx && npx vitest list tests/viz/TokenBudgetBar.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/TokenBudgetBar.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: TokenBudgetBar. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-026 implements it.

## Context
Stub `services/web/src/viz/TokenBudgetBar.tsx` (signature and props are final):
```tsx
import type { GenerateArtifact } from '../api/types'

export interface TokenBudgetBarProps {
  budget: GenerateArtifact['budget']
}

/**
 * Stacked horizontal bar of max_context_tokens: system (grey), question (blue), context (green), free
 * (white). Each segment has data-testid="seg-<name>" and width % of max. Text "<used total> /
 * <max_context_tokens> tokens (approx.) · <chunks_included> chunks included, <chunks_dropped>
 * dropped" where used total = system + question + used_context.
 */
export function TokenBudgetBar(_props: TokenBudgetBarProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. GENERATE.budget → text '143 / 4000 tokens (approx.) · 2 chunks included, 1 dropped'
2. segment widths: seg-system 1.5%, seg-question 0.2%, seg-context 1.875%
3. used > max → widths capped so the sum is 100%

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
