---
id: T-web-003t
kind: test
feature: F-qdrant-browser
title: 'Write tests: api wrappers qdrant.ts'
service: web
depends_on: []
edit:
- services/web/tests/api/qdrant.test.ts
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/api/qdrant.test.ts && npx eslint tests/api/qdrant.test.ts && npx vitest list tests/api/qdrant.test.ts'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/api/qdrant.test.ts
max_attempts: 3
---

## Goal
Write unit tests for: api wrappers qdrant.ts. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-003 implements it.

## Context
Implement with `apiFetch` from src/api/client.ts (it prefixes /api/v1, sends JSON, throws ApiError). Paths and bodies: contracts/openapi/api.yaml.

Stub `services/web/src/api/qdrant.ts` (signature and props are final):
```tsx
import type { FacetResponse, PayloadFilter, QdrantInfo, QdrantPoint, ScrollResponse } from './types'

export function getQdrantInfo(_collectionId: string): Promise<QdrantInfo> {
  throw new Error('not implemented')
}

/** POST /collections/{id}/qdrant/scroll. */
export function scrollPoints(
  _collectionId: string,
  _req: { filter: PayloadFilter; limit: number; offset: string | null; with_vectors: boolean },
): Promise<ScrollResponse> {
  throw new Error('not implemented')
}

/** POST /collections/{id}/qdrant/count → number. */
export function countPoints(_collectionId: string, _filter: PayloadFilter): Promise<number> {
  throw new Error('not implemented')
}

export function getFacet(_collectionId: string, _key: string): Promise<FacetResponse> {
  throw new Error('not implemented')
}

export function getPoint(_collectionId: string, _pointId: string): Promise<QdrantPoint> {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. getQdrantInfo(c) → GET /api/v1/collections/c/qdrant
2. scrollPoints(c, req) → POST /collections/c/qdrant/scroll with req as body
3. countPoints(c, f) → POST /collections/c/qdrant/count { filter: f } and resolves to the number
4. getFacet(c, 'tags') → GET /collections/c/qdrant/facets/tags
5. getPoint(c, 'abc') → GET /collections/c/qdrant/points/abc; 404 → ApiError POINT_NOT_FOUND

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
