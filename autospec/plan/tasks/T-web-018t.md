---
id: T-web-018t
kind: test
feature: F-chunk
title: 'Write tests: ChunkHighlighter'
service: web
depends_on: []
edit:
- services/web/tests/viz/ChunkHighlighter.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/viz/ChunkHighlighter.test.tsx && npx eslint tests/viz/ChunkHighlighter.test.tsx && npx vitest list tests/viz/ChunkHighlighter.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/ChunkHighlighter.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: ChunkHighlighter. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-018 implements it.

## Context
Stub `services/web/src/viz/ChunkHighlighter.tsx` (signature and props are final):
```tsx
import type { ChunkArtifact } from '../api/types'

export interface ChunkHighlighterProps {
  sourceText: string
  chunks: ChunkArtifact['chunks']
  selectedIndex?: number | null
  onSelect?: (index: number) => void
}

/**
 * Renders sourceText as segments split at every chunk char_start/char_end boundary. Each segment's
 * background = CHUNK_COLORS[first covering chunk index % 10]; a segment covered by ≥2 chunks (overlap)
 * gets data-overlap="true" and a striped/darker style; uncovered segments plain. Each segment
 * <span data-chunks="0,1"> lists covering indices. Click → onSelect(lowest covering index). Chunks with
 * char_start null are listed below as "Chunks without a source position" cards.
 */
export function ChunkHighlighter(_props: ChunkHighlighterProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. CHUNK fixture (chunk 0 and 1 overlap) → some span has data-overlap 'true' and data-chunks '0,1'
2. spans concatenated text == sourceText
3. click a span covering chunks '1,2' → onSelect(1)
4. chunk with char_start null → listed under 'Chunks without a source position'

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
