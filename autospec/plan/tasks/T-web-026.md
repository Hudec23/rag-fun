---
id: T-web-026
kind: impl
feature: F-generate
title: TokenBudgetBar
service: web
depends_on:
- T-web-026t
edit:
- services/web/src/viz/TokenBudgetBar.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/viz/TokenBudgetBar.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/viz/TokenBudgetBar.tsx && npx eslint src/viz/TokenBudgetBar.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/TokenBudgetBar.test.tsx
max_attempts: 3
---

## Goal
Implement: TokenBudgetBar. The tests written by T-web-026t define done.

## Context
Stub `services/web/src/viz/TokenBudgetBar.tsx` (signature and props are final):
```tsx
import type { GenerateArtifact } from '../api/types'

export interface TokenBudgetBarProps {
  budget: GenerateArtifact['budget']
}

/**
 * Stacked horizontal bar of max_context_tokens: system (grey), question (blue), context (green), free
 * (white). Each segment has data-testid="seg-<name>" and width % of max. Text "<used total> /
 * <max_context_tokens> tokens (approx.) · <chunks_included> chunks included, <chunks_dropped>
 * dropped" where used total = system + question + used_context.
 */
export function TokenBudgetBar(_props: TokenBudgetBarProps): React.ReactElement {
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
