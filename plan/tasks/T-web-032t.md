---
id: T-web-032t
kind: test
feature: F-store
title: 'Write tests: StoreView'
service: web
depends_on: []
edit:
- services/web/tests/stages/StoreView.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/stages/StoreView.test.tsx && npx eslint tests/stages/StoreView.test.tsx && npx vitest list tests/stages/StoreView.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/stages/StoreView.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: StoreView. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-032 implements it.

## Context
Fixtures from tests/setup/fixtures.ts; derive variants with spread, e.g. { ...CHUNK, strategy: 'semantic', semantic: {...} }.

Stub `services/web/src/components/stages/StoreView.tsx` (signature and props are final):
```tsx
import type { StoreArtifact } from '../../api/types'

export interface StoreViewProps {
  stageRunId: string
  artifact: StoreArtifact
  collectionId?: string
}

/**
 * Summary: "<points_written> points written to <qdrant_collection>" (+ "<points_deleted> old
 * points replaced" when > 0). Vector config table (dense name/size/distance, sparse name/modifier).
 * Payload sample as pretty JSON (<pre>) with filterable keys (meta.*) highlighted. Link "Open in Qdrant
 * browser" → /qdrant/<collectionId>.
 */
export function StoreView(_props: StoreViewProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. '4 points written to rf_…'
2. vector config table shows text-dense 384 Cosine and text-sparse idf
3. payload sample <pre> contains 'meta'
4. points_deleted > 0 → '<n> old points replaced'

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
