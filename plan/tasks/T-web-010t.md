---
id: T-web-010t
kind: test
feature: F-stage-flow
title: 'Write tests: StageStepper'
service: web
depends_on: []
edit:
- services/web/tests/components/StageStepper.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/components/StageStepper.test.tsx && npx eslint tests/components/StageStepper.test.tsx && npx vitest list tests/components/StageStepper.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/components/StageStepper.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: StageStepper. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-010 implements it.

## Context
Build StageRun values with stageRun() from tests/setup/fixtures.ts.

Stub `services/web/src/components/StageStepper.tsx` (signature and props are final):
```tsx
import type { StageRun } from '../api/types'

export interface StageStepperProps {
  stages: { name: string; run: StageRun | null }[]
  selected: string
  onSelect: (stage: string) => void
}

/**
 * Horizontal steps in the given order. Each step is a button with the stage name and a status badge:
 * "not run" when run is null, else run.status (+ " v<version>"). Badge colors: done green, failed red,
 * running/queued blue (with animate-pulse), stale amber. aria-current="step" on the selected one.
 */
export function StageStepper(_props: StageStepperProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. 4 stages, parse done v2, chunk stale v1, embed null, store failed → badges 'done v2', 'stale v1', 'not run', 'failed v1'
2. selected 'chunk' → that button has aria-current 'step'
3. click 'embed' → onSelect('embed')
4. running status badge has class animate-pulse

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
