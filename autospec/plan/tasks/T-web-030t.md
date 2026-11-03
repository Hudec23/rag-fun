---
id: T-web-030t
kind: test
feature: F-chunk
title: 'Write tests: ChunkView'
service: web
depends_on:
- T-web-018
- T-web-019
edit:
- services/web/tests/stages/ChunkView.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/stages/ChunkView.test.tsx && npx eslint tests/stages/ChunkView.test.tsx && npx vitest list tests/stages/ChunkView.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/stages/ChunkView.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: ChunkView. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-030 implements it.

## Context
Fixtures from tests/setup/fixtures.ts; derive variants with spread, e.g. { ...CHUNK, strategy: 'semantic', semantic: {...} }.

Stub `services/web/src/components/stages/ChunkView.tsx` (signature and props are final):
```tsx
import type { ChunkArtifact } from '../../api/types'

export interface ChunkViewProps {
  stageRunId: string
  artifact: ChunkArtifact
}

/**
 * Header: "<count> chunks · <min>–<max> chars · mean <mean>" + strategy name. Tabs are
 * <button role="tab"> (accessible name = label) above one <div role="tabpanel">: "Source"
 * (<ChunkHighlighter>), "Cards" (one card per chunk: #index, element_type badge, pages, section path
 * joined ' › ', text), "Histogram" (<LengthHistogram>). Semantic strategy: extra tab "Breakpoints"
 * listing gaps with distance (3 decimals) and a ✂ marker where is_break.
 */
export function ChunkView(_props: ChunkViewProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. header '4 chunks · <min>–<max> chars · mean <mean>' and 'recursive'
2. tabs Source / Cards / Histogram; Cards shows '#0' with section path joined by ' › '
3. semantic artifact (fixture with semantic gaps) → 'Breakpoints' tab with ✂ markers

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
