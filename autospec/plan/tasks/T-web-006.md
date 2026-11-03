---
id: T-web-006
kind: impl
feature: F-live-progress
title: useIngestRun + useQueryRun live hooks
service: web
depends_on:
- T-web-006t
- T-web-002
- T-web-005
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
- T-api-020
- T-worker-017
edit:
- services/web/src/hooks/useRun.ts
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/hooks/useRun.test.tsx
- tests/e2e/test_events.py
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/hooks/useRun.ts && npx eslint src/hooks/useRun.ts'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/hooks/useRun.test.tsx
- docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml up -d --build --wait && docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml --profile e2e run --rm e2e pytest -q /workspace/tests/e2e/test_events.py
max_attempts: 3
---

## Goal
Implement: useIngestRun + useQueryRun live hooks. The tests written by T-web-006t define done.

## Context
renderHook wrapped in a QueryClientProvider (create the wrapper in the test).

Stub `services/web/src/hooks/useRun.ts` (signature and props are final):
```tsx
import type { IngestRun, QueryRun } from '../api/types'

export interface LiveRun<T> {
  run: T | undefined
  error: unknown
  /** latest stage.progress per stage_run_id */
  progress: Record<string, { done: number; total: number; message: string }>
  /** generate.token texts joined in index order per stage_run_id */
  tokens: Record<string, string>
}

/** react-query ['ingest-run', runId] via getIngestRun + useRunEvents: run.updated, stage.started,
 * stage.completed, stage.failed → invalidate the query; stage.progress → progress map. */
export function useIngestRun(_runId: string): LiveRun<IngestRun> {
  throw new Error('not implemented')
}

/** Same for query runs (['query-run', runId], getQueryRun); generate.token → tokens map. */
export function useQueryRun(_runId: string): LiveRun<QueryRun> {
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
