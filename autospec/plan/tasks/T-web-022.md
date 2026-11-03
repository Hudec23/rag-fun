---
id: T-web-022
kind: impl
feature: F-embed
title: ScatterPlot
service: web
depends_on:
- T-web-022t
edit:
- services/web/src/viz/ScatterPlot.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/viz/ScatterPlot.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/viz/ScatterPlot.tsx && npx eslint src/viz/ScatterPlot.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/ScatterPlot.test.tsx
max_attempts: 3
---

## Goal
Implement: ScatterPlot. The tests written by T-web-022t define done.

## Context
Stub `services/web/src/viz/ScatterPlot.tsx` (signature and props are final):
```tsx
export interface ScatterPlotProps {
  points2d: number[][] | null
  points3d: number[][] | null
  labels: string[]
  groups: string[]
  method: 'pca' | 'umap'
}

/**
 * Toggle buttons "2D" / "3D" (default 2D). 2D → Plotly 'scatter' mode markers; 3D → 'scatter3d'.
 * One trace per distinct group (legend), hover text = labels[i]. Selected dimension's points null →
 * message "Not enough chunks for <METHOD> <2D|3D>". Title "<PCA|UMAP> projection".
 */
export function ScatterPlot(_props: ScatterPlotProps): React.ReactElement {
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
