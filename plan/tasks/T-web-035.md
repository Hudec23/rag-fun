---
id: T-web-035
kind: impl
feature: F-rerank
title: RerankView
service: web
depends_on:
- T-web-035t
- T-web-025
- T-api-001
- T-api-002
- T-api-003
- T-api-004
- T-api-005
- T-api-008
- T-api-009
- T-api-010
- T-api-011
- T-api-012
- T-api-013
- T-api-014
- T-api-015
- T-api-016
- T-api-018
- T-api-019
- T-api-026
- T-api-027
- T-worker-005
- T-worker-006
- T-worker-007
- T-worker-008
- T-worker-009
- T-worker-012
- T-worker-017
- T-worker-022
- T-worker-025
- T-worker-027
- T-api-017
- T-worker-033
- T-worker-035
edit:
- services/web/src/components/stages/RerankView.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/stages/RerankView.test.tsx
- services/web/tests/acceptance/RerankView.test.tsx
- tests/e2e/test_rerank.py
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/components/stages/RerankView.tsx && npx eslint src/components/stages/RerankView.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/stages/RerankView.test.tsx tests/acceptance/RerankView.test.tsx
- docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml up -d --build --wait && docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml --profile e2e run --rm e2e pytest -q /workspace/tests/e2e/test_rerank.py
max_attempts: 3
---

## Goal
Implement: RerankView. The tests written by T-web-035t define done.

## Context
Fixtures from tests/setup/fixtures.ts; derive variants with spread, e.g. { ...CHUNK, strategy: 'semantic', semantic: {...} }.

Stub `services/web/src/components/stages/RerankView.tsx` (signature and props are final):
```tsx
import type { RerankArtifact } from '../../api/types'

export interface RerankViewProps {
  stageRunId: string
  artifact: RerankArtifact
}

/**
 * Header "<model> · top <top_n>" (or disabled banner via RerankDiff) then <RerankDiff>.
 */
export function RerankView(_props: RerankViewProps): React.ReactElement {
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
