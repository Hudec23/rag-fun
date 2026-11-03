---
id: T-web-025
kind: impl
feature: F-rerank
title: RerankDiff
service: web
depends_on:
- T-web-025t
edit:
- services/web/src/viz/RerankDiff.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/viz/RerankDiff.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/viz/RerankDiff.tsx && npx eslint src/viz/RerankDiff.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/RerankDiff.test.tsx
max_attempts: 3
---

## Goal
Implement: RerankDiff. The tests written by T-web-025t define done.

## Context
Stub `services/web/src/viz/RerankDiff.tsx` (signature and props are final):
```tsx
import type { RerankArtifact } from '../api/types'

export interface RerankDiffProps {
  artifact: RerankArtifact
}

/**
 * Two columns "Before" (artifact.before) and "After" (artifact.after[].hit). After rows show
 * "↑3" (green) / "↓2" (red) / "=" from previous_rank − new rank, plus rerank_score (4 decimals) or "—".
 * disabled → banner "Reranking disabled — showing retrieval order".
 */
export function RerankDiff(_props: RerankDiffProps): React.ReactElement {
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
