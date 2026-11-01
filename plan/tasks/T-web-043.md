---
id: T-web-043
kind: impl
feature: F-generate
title: QueryPage
service: web
depends_on:
- T-web-043t
- T-web-006
- T-web-010
- T-web-037
- T-web-033
- T-web-034
- T-web-035
- T-web-036
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
- T-worker-029
- T-worker-033
- T-worker-035
- T-worker-038
edit:
- services/web/src/pages/QueryPage.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/pages/QueryPage.test.tsx
- services/web/tests/acceptance/GenerateView.test.tsx
- tests/e2e/test_generate.py
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/pages/QueryPage.tsx && npx eslint src/pages/QueryPage.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/pages/QueryPage.test.tsx tests/acceptance/GenerateView.test.tsx
- docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml up -d --build --wait && docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml --profile e2e run --rm e2e pytest -q /workspace/tests/e2e/test_generate.py
max_attempts: 3
---

## Goal
Implement: QueryPage. The tests written by T-web-043t define done.

## Context
Stub `services/web/src/pages/QueryPage.tsx` (signature and props are final):
```tsx
/**
 * Route "/query" (new) and "/query/:runId". New: collection select + question textarea + "Ask" →
 * createQueryRun → navigate to /query/<id>. With runId: useQueryRun; header with the question and
 * "Run all" (runAllQuery equivalent: POST /query-runs/{id}/run-all via startQueryStage chain is NOT
 * used — call apiFetch run-all with from_stage null and defaults); <StageStepper> transform/retrieve/
 * rerank/generate + selected <StagePanel> (generate gets liveText from tokens).
 */
export function QueryPage(): React.ReactElement {
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
