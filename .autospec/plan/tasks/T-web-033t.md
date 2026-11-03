---
id: T-web-033t
kind: test
feature: F-transform
title: 'Write tests: TransformView'
service: web
depends_on: []
edit:
- services/web/tests/stages/TransformView.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/stages/TransformView.test.tsx && npx eslint tests/stages/TransformView.test.tsx && npx vitest list tests/stages/TransformView.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/stages/TransformView.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: TransformView. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-033 implements it.

## Context
Fixtures from tests/setup/fixtures.ts; derive variants with spread, e.g. { ...CHUNK, strategy: 'semantic', semantic: {...} }.

Stub `services/web/src/components/stages/TransformView.tsx` (signature and props are final):
```tsx
import type { TransformArtifact } from '../../api/types'

export interface TransformViewProps {
  stageRunId: string
  artifact: TransformArtifact
}

/**
 * Strategy name; "Original question" box; list "Search queries" (queries[]); for hyde the
 * hypothetical document in a quote block; collapsible "Prompt" showing messages (role + content).
 * strategy none → "No transformation — the question is used as is."
 */
export function TransformView(_props: TransformViewProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. queries listed under 'Search queries'
2. hyde artifact → quote block with hyde_document
3. strategy none → 'No transformation — the question is used as is.'
4. 'Prompt' collapsible shows system message

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
