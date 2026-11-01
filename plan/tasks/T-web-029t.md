---
id: T-web-029t
kind: test
feature: F-parse
title: 'Write tests: ParseView'
service: web
depends_on:
- T-web-017
edit:
- services/web/tests/stages/ParseView.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/stages/ParseView.test.tsx && npx eslint tests/stages/ParseView.test.tsx && npx vitest list tests/stages/ParseView.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/stages/ParseView.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: ParseView. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-029 implements it.

## Context
Fixtures from tests/setup/fixtures.ts; derive variants with spread, e.g. { ...CHUNK, strategy: 'semantic', semantic: {...} }.

Stub `services/web/src/components/stages/ParseView.tsx` (signature and props are final):
```tsx
import type { ParseArtifact } from '../../api/types'

export interface ParseViewProps {
  stageRunId: string
  artifact: ParseArtifact
}

/**
 * Left: page selector (pages[]) + <PageWithBoxes> using pageImageUrl(stageRunId, page). Right:
 * element list for the page (type badge in ELEMENT_COLORS, text); selecting an element in either place
 * selects it in both. Tables render as an HTML <table> from table.cells (header cells as <th>).
 * Header line: "<n> pages · <m> elements · <t> tables" + "OCR used" badge when ocr_used. Formats
 * without pages: just the element list.
 */
export function ParseView(_props: ParseViewProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. 2 pages · 8 elements · 0 tables
2. page select switches to page 2 boxes
3. selecting an element in the list highlights its box
4. tables render as <table> with <th> header cells (use a modified fixture with a table element)

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
