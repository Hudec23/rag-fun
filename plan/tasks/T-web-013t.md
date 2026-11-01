---
id: T-web-013t
kind: test
feature: F-qdrant-browser
title: 'Write tests: FilterBuilder'
service: web
depends_on:
- T-web-003
edit:
- services/web/tests/components/FilterBuilder.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/components/FilterBuilder.test.tsx && npx eslint tests/components/FilterBuilder.test.tsx && npx vitest list tests/components/FilterBuilder.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/components/FilterBuilder.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: FilterBuilder. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-013 implements it.

## Context
Stub `services/web/src/components/FilterBuilder.tsx` (signature and props are final):
```tsx
import type { PayloadFilter } from '../api/types'

export interface FilterBuilderProps {
  collectionId: string
  value: PayloadFilter
  onChange: (f: PayloadFilter) => void
}

/**
 * Edits value.must only. Rows: key select (file_id, batch_id, tags, mime, element_type, chunk_strategy,
 * parse_strategy, page, chunk_index) + operator: keyword keys → "is any of" with a multi-select whose
 * options come from getFacet(collectionId, key) ("value (count)"); page/chunk_index → "between" with two
 * number inputs (gte/lte, empty = omitted). "Add condition" button appends {key: 'tags', match: {any: []}}
 * (not emitted until it has ≥1 value); "×" removes a row. Emits only complete conditions.
 */
export function FilterBuilder(_props: FilterBuilderProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. click 'Add condition' → a row with key select 'tags'; nothing emitted yet
2. facet GET /collections/c/qdrant/facets/tags → options 'finance (4)'; selecting finance → onChange({ must: [{ key: 'tags', match: { any: ['finance'] } }] })
3. key 'page' → 'between' with two number inputs; gte 1 → onChange({ must: [{ key: 'page', range: { gte: 1 } }] })
4. '×' removes the row → onChange({ must: [] })
5. value prop with an existing condition renders it pre-filled

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
