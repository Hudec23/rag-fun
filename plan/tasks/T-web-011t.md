---
id: T-web-011t
kind: test
feature: F-stage-flow
title: 'Write tests: VersionPicker'
service: web
depends_on:
- T-web-002
edit:
- services/web/tests/components/VersionPicker.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/components/VersionPicker.test.tsx && npx eslint tests/components/VersionPicker.test.tsx && npx vitest list tests/components/VersionPicker.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/components/VersionPicker.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: VersionPicker. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-011 implements it.

## Context
Stub `services/web/src/components/VersionPicker.tsx` (signature and props are final):
```tsx
import type { Stage } from '../api/types'

export interface VersionPickerProps {
  runId: string
  stage: Stage
  selectedId: string | null
  onSelect: (stageRunId: string) => void
}

/**
 * <select aria-label="Version"> listing listStageRuns(runId, stage) items as "v<version> · <status>",
 * newest first; value = selectedId; change → onSelect(id). Hidden when there are < 2 versions.
 */
export function VersionPicker(_props: VersionPickerProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. GET /api/v1/stage-runs?run_id=…&stage=parse returns v2, v1 → select 'Version' with options 'v2 · done', 'v1 · failed' in that order
2. choosing 'v1 · failed' → onSelect(v1 id)
3. only one version → nothing rendered (no 'Version' select)

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
