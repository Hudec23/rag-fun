---
id: T-web-028
kind: impl
feature: F-pipeline-graph
title: PipelineGraph
service: web
depends_on:
- T-web-028t
edit:
- services/web/src/viz/PipelineGraph.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/viz/PipelineGraph.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/viz/PipelineGraph.tsx && npx eslint src/viz/PipelineGraph.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/PipelineGraph.test.tsx
max_attempts: 3
---

## Goal
Implement: PipelineGraph. The tests written by T-web-028t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, src/api/schema.d.ts, package.json or package-lock.json.
- Do not add dependencies; Tailwind classes only for styling.
- Do not change exported names or props.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
