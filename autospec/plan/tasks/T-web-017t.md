---
id: T-web-017t
kind: test
feature: F-parse
title: 'Write tests: PageWithBoxes'
service: web
depends_on: []
edit:
- services/web/tests/viz/PageWithBoxes.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/viz/PageWithBoxes.test.tsx && npx eslint tests/viz/PageWithBoxes.test.tsx && npx vitest list tests/viz/PageWithBoxes.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/PageWithBoxes.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: PageWithBoxes. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-017 implements it.

## Context
Stub `services/web/src/viz/PageWithBoxes.tsx` (signature and props are final):
```tsx
import type { ParseArtifact } from '../api/types'

export interface PageWithBoxesProps {
  imageUrl: string | null
  width: number
  height: number
  elements: ParseArtifact['elements']
  selectedId?: string | null
  onSelect?: (elementId: string) => void
}

/**
 * Page image (<img alt="page">) in a relative container; for every element with a bbox an absolutely
 * positioned <div data-testid="bbox" data-element-id=…> at left/top/width/height in % of the page
 * (l/width*100, t/height*100, (r-l)/width*100, (b-t)/height*100), border color ELEMENT_COLORS[type],
 * title = "<type>: <first 80 chars of text>". Click → onSelect(id). selectedId gets a thicker border.
 * imageUrl null → grey placeholder "No page image" with the boxes still drawn on a width:height box.
 * Legend below: one entry per element type present.
 */
export function PageWithBoxes(_props: PageWithBoxesProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. PARSE page 1 elements (5 with bbox) → 5 [data-testid=bbox]; first box style left '11.764…%' (72/612*100) top ≈ 7.58% (60/792)
2. box border color == ELEMENT_COLORS[type]
3. click a box → onSelect(its id); selectedId box has a thicker border (border-width differs)
4. imageUrl null → 'No page image' and boxes still rendered
5. legend lists 'heading' and 'text'

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
