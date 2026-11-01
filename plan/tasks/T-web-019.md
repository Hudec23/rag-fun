---
id: T-web-019
kind: impl
feature: F-chunk
title: LengthHistogram
service: web
depends_on:
- T-web-019t
edit:
- services/web/src/viz/LengthHistogram.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/viz/LengthHistogram.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/viz/LengthHistogram.tsx && npx eslint src/viz/LengthHistogram.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/LengthHistogram.test.tsx
max_attempts: 3
---

## Goal
Implement: LengthHistogram. The tests written by T-web-019t define done.

## Context
Stub `services/web/src/viz/LengthHistogram.tsx` (signature and props are final):
```tsx
export interface LengthHistogramProps {
  binEdges: number[]
  counts: number[]
}

/**
 * Plotly bar chart (react-plotly.js <Plot>): x = bin centers ((edge[i]+edge[i+1])/2), y = counts,
 * width = bin width, layout title "Chunk length (chars)". Empty counts → text "No chunks".
 */
export function LengthHistogram(_props: LengthHistogramProps): React.ReactElement {
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
