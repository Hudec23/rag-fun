---
id: T-web-024
kind: impl
feature: F-retrieve
title: HybridLists
service: web
depends_on:
- T-web-024t
edit:
- services/web/src/viz/HybridLists.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/viz/HybridLists.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/viz/HybridLists.tsx && npx eslint src/viz/HybridLists.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/HybridLists.test.tsx
max_attempts: 3
---

## Goal
Implement: HybridLists. The tests written by T-web-024t define done.

## Context
Stub `services/web/src/viz/HybridLists.tsx` (signature and props are final):
```tsx
import type { RetrieveArtifact } from '../api/types'

export interface HybridListsProps {
  artifact: RetrieveArtifact
}

/**
 * Three columns for per_query[0] (with a query selector when per_query.length > 1): "Dense", "Sparse"
 * (column omitted when the list is null), "Fused (RRF)" from artifact.fused. Each row: rank, score (4
 * decimals), first 120 chars, filename + page. Hovering/clicking a row highlights the same doc_id in all
 * columns (data-highlighted="true"). Fused rows show source ranks as "D#2 S#5".
 */
export function HybridLists(_props: HybridListsProps): React.ReactElement {
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
