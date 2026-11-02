---
id: T-web-031t
kind: test
feature: F-embed
title: 'Write tests: EmbedView'
service: web
depends_on:
- T-web-020
- T-web-021
- T-web-022
- T-web-023
edit:
- services/web/tests/stages/EmbedView.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/stages/EmbedView.test.tsx && npx eslint tests/stages/EmbedView.test.tsx && npx vitest list tests/stages/EmbedView.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/stages/EmbedView.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: EmbedView. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-031 implements it.

## Context
Fixtures from tests/setup/fixtures.ts; derive variants with spread, e.g. { ...CHUNK, strategy: 'semantic', semantic: {...} }.

Stub `services/web/src/components/stages/EmbedView.tsx` (signature and props are final):
```tsx
import type { ChunkArtifact, EmbedArtifact } from '../../api/types'

export interface EmbedViewProps {
  stageRunId: string
  artifact: EmbedArtifact
  chunks?: ChunkArtifact['chunks']
}

/**
 * Header: "<n> chunks · <dense_model> (<dims>d) · <sparse_model>" + "<k> over limit" badge. Tabs are
 * <button role="tab"> (accessible name = label) above one <div role="tabpanel">: "Tokens" (chunk
 * selector + <TokenView>), "Heatmap" (<VectorHeatmap> of sampled chunks' dense vectors, labels "#index"),
 * "Projection" (two buttons named exactly "PCA" and "UMAP", default PCA, + <ScatterPlot>; groups =
 * element_type of props.chunks when given, else 'chunk'), "Similarity" (<SimilarityMatrix> labels
 * "#index"). Notice: "Vectors are not stored yet — run Store to write them to Qdrant."
 */
export function EmbedView(_props: EmbedViewProps): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. '4 chunks · all-minilm (384d) · Qdrant/bm25' and '1 over limit'
2. Tokens tab: chunk selector switches TokenView
3. Projection tab PCA uses projections.pca2; UMAP null → not-enough message
4. Similarity tab renders SimilarityMatrix

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
