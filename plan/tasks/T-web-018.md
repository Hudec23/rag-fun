---
id: T-web-018
kind: impl
feature: F-chunk
title: ChunkHighlighter
service: web
depends_on:
- T-web-018t
edit:
- services/web/src/viz/ChunkHighlighter.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/viz/ChunkHighlighter.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/viz/ChunkHighlighter.tsx && npx eslint src/viz/ChunkHighlighter.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/ChunkHighlighter.test.tsx
max_attempts: 3
---

## Goal
Implement: ChunkHighlighter. The tests written by T-web-018t define done.

## Context
Stub `services/web/src/viz/ChunkHighlighter.tsx` (signature and props are final):
```tsx
import type { ChunkArtifact } from '../api/types'

export interface ChunkHighlighterProps {
  sourceText: string
  chunks: ChunkArtifact['chunks']
  selectedIndex?: number | null
  onSelect?: (index: number) => void
}

/**
 * Renders sourceText as segments split at every chunk char_start/char_end boundary. Each segment's
 * background = CHUNK_COLORS[first covering chunk index % 10]; a segment covered by ≥2 chunks (overlap)
 * gets data-overlap="true" and a striped/darker style; uncovered segments plain. Each segment
 * <span data-chunks="0,1"> lists covering indices. Click → onSelect(lowest covering index). Chunks with
 * char_start null are listed below as "Chunks without a source position" cards.
 */
export function ChunkHighlighter(_props: ChunkHighlighterProps): React.ReactElement {
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
