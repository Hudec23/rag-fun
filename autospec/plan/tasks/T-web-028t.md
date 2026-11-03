---
id: T-web-028t
kind: test
feature: F-pipeline-graph
title: 'Write tests: PipelineGraph'
service: web
depends_on: []
edit:
- services/web/tests/viz/PipelineGraph.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/viz/PipelineGraph.test.tsx && npx eslint tests/viz/PipelineGraph.test.tsx && npx vitest list tests/viz/PipelineGraph.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/PipelineGraph.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: PipelineGraph. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-028 implements it.

## Context
@xyflow/react renders in jsdom with the global ResizeObserver stub; give the container a fixed height style.

Stub `services/web/src/viz/PipelineGraph.tsx` (signature and props are final):
```tsx
import type { PipelineGraph } from '../api/types'

export interface PipelineGraphProps {
  graph: PipelineGraph
}

/**
 * @xyflow/react <ReactFlow> read-only: one node per graph.nodes (label = name, sublabel = class name
 * after the last '.', custom nodes highlighted with a purple border and "custom" badge), one edge per
 * graph.edges (label "sender_socket → receiver_socket"). Layout: nodes left-to-right in topological
 * order (x = depth*260, y = index within depth*110). Clicking a node shows its init_params as a
 * name/value table beside the graph.
 */
export function PipelineGraph(_props: PipelineGraphProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. GRAPH → node labels 'annotator' and 'splitter', class names 'ChunkAnnotator' and 'DocumentSplitter'
2. custom node shows 'custom' badge
3. edge label 'documents → documents'
4. click 'splitter' → init params table with 'split_by' and '"word"'

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
