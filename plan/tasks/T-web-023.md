---
id: T-web-023
kind: impl
feature: F-embed
title: SimilarityMatrix
service: web
depends_on:
- T-web-023t
edit:
- services/web/src/viz/SimilarityMatrix.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/viz/SimilarityMatrix.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/viz/SimilarityMatrix.tsx && npx eslint src/viz/SimilarityMatrix.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/SimilarityMatrix.test.tsx
max_attempts: 3
---

## Goal
Implement: SimilarityMatrix. The tests written by T-web-023t define done.

## Context
Stub `services/web/src/viz/SimilarityMatrix.tsx` (signature and props are final):
```tsx
export interface SimilarityMatrixProps {
  matrix: number[][]
  labels: string[]
}

/**
 * Plotly heatmap, z = matrix, x = y = labels, zmin -1, zmax 1, colorscale 'Viridis', title
 * "Cosine similarity". Below: the 5 most similar off-diagonal pairs (i<j) as "<label i> ↔ <label j>:
 * <value to 3 decimals>", sorted desc. Empty → "No vectors".
 */
export function SimilarityMatrix(_props: SimilarityMatrixProps): React.ReactElement {
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
