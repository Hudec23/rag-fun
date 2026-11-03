---
id: T-web-012t
kind: test
feature: F-stage-flow
title: 'Write tests: ParamsForm'
service: web
depends_on: []
edit:
- services/web/tests/components/ParamsForm.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/components/ParamsForm.test.tsx && npx eslint tests/components/ParamsForm.test.tsx && npx vitest list tests/components/ParamsForm.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/components/ParamsForm.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: ParamsForm. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-012 implements it.

## Context
Stub `services/web/src/components/ParamsForm.tsx` (signature and props are final):
```tsx
import type { Stage } from '../api/types'

export interface ParamsFormProps {
  stage: Stage
  value: Record<string, unknown>
  onChange: (v: Record<string, unknown>) => void
}

/**
 * Generic params editor for every stage (except retrieve filters, handled by FilterBuilder).
 * parse/chunk/transform: first a "Strategy" select (parse: docling_layout|docling_ocr|plain_text, chunk:
 * fixed|sentence|recursive|semantic|structure|table, transform: none|rewrite|multi_query|hyde); changing
 * it resets value to lib/defaults for that strategy. Then one labelled input per remaining field of the
 * current value: number → <input type="number"> (label = field name), boolean → checkbox, string enum
 * (split_by, mode) → select, string[] (separators) → comma-separated text input showing "\n" for
 * newlines. Emits a new object on every change (numbers parsed with Number()).
 */
export function ParamsForm(_props: ParamsFormProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. stage chunk with CHUNK_DEFAULTS.recursive → 'Strategy' select value 'recursive', number inputs 'length' 1000 and 'overlap' 100, text input 'separators'
2. change Strategy to 'semantic' → onChange(CHUNK_DEFAULTS.semantic)
3. type in 'length' → onChange with length as a number
4. stage parse docling_layout → checkboxes 'extract_tables' and 'page_images'; toggling emits false
5. stage embed → only a 'batch_size' number input, no Strategy select
6. stage retrieve → 'mode' select with dense/sparse/hybrid; the filters field is not rendered

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
