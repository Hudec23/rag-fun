---
id: T-web-003
kind: impl
feature: F-qdrant-browser
title: api wrappers qdrant.ts
service: web
depends_on:
- T-web-003t
edit:
- services/web/src/api/qdrant.ts
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/api/qdrant.test.ts
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/api/qdrant.ts && npx eslint src/api/qdrant.ts'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/api/qdrant.test.ts
max_attempts: 3
---

## Goal
Implement: api wrappers qdrant.ts. The tests written by T-web-003t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, src/api/schema.d.ts, package.json or package-lock.json.
- Do not add dependencies; Tailwind classes only for styling.
- Do not change exported names or props.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
