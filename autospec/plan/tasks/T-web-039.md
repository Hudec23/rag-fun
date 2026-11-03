---
id: T-web-039
kind: impl
feature: F-stage-flow
title: IngestRunPage
service: web
depends_on:
- T-web-039t
- T-web-006
- T-web-010
- T-web-037
- T-web-029
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
edit:
- services/web/src/pages/IngestRunPage.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/pages/IngestRunPage.test.tsx
- services/web/tests/acceptance/IngestRun.test.tsx
- tests/e2e/test_stage_flow.py
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/pages/IngestRunPage.tsx && npx eslint src/pages/IngestRunPage.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/pages/IngestRunPage.test.tsx tests/acceptance/IngestRun.test.tsx
- docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml up -d --build --wait && docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml --profile e2e run --rm e2e pytest -q /workspace/tests/e2e/test_stage_flow.py
max_attempts: 3
---

## Goal
Implement: IngestRunPage. The tests written by T-web-039t define done.

## Context
Stub `services/web/src/pages/IngestRunPage.tsx` (signature and props are final):
```tsx
/**
 * Route "/ingest/:runId". useIngestRun(runId). Header: filename, collection, "Run all" button
 * (runAllIngest(runId, null, current params of each stage or INGEST_DEFAULTS)) and pending plan chips.
 * <StageStepper> for parse/chunk/embed/store and the selected <StagePanel>. Default selection = first
 * stage not done (else store), computed ONCE when the run first loads; afterwards only the user changes
 * it. The panel gets run = run.stages[stage] and progress = live.progress[that stage run's id]. Passes
 * extra.chunks (from the active chunk artifact) to the embed panel and extra.collectionId to store.
 * Loading/error states as in CollectionsPage.
 */
export function IngestRunPage(): React.ReactElement {
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
