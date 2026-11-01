---
id: T-web-021
kind: impl
feature: F-embed
title: VectorHeatmap
service: web
depends_on:
- T-web-021t
edit:
- services/web/src/viz/VectorHeatmap.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/viz/VectorHeatmap.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/viz/VectorHeatmap.tsx && npx eslint src/viz/VectorHeatmap.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/VectorHeatmap.test.tsx
max_attempts: 3
---

## Goal
Implement: VectorHeatmap. The tests written by T-web-021t define done.

## Context
Stub `services/web/src/viz/VectorHeatmap.tsx` (signature and props are final):
```tsx
export interface VectorHeatmapProps {
  vectors: number[][]
  labels: string[]
}

/**
 * Plotly heatmap: z = vectors (rows = chunks, labels on y), x = dimension index, colorscale 'RdBu',
 * zmid 0, layout title "Dense vectors (<n> × <dims>)". Empty → "No vectors".
 */
export function VectorHeatmap(_props: VectorHeatmapProps): React.ReactElement {
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
