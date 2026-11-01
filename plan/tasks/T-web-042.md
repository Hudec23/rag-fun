---
id: T-web-042
kind: impl
feature: F-pipeline-graph
title: PipelinesPage
service: web
depends_on:
- T-web-042t
- T-web-004
- T-web-028
- T-api-025
- T-api-026
- T-worker-039
edit:
- services/web/src/pages/PipelinesPage.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/pages/PipelinesPage.test.tsx
- services/web/tests/acceptance/Pipelines.test.tsx
- tests/e2e/test_pipeline_graphs.py
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/pages/PipelinesPage.tsx && npx eslint src/pages/PipelinesPage.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/pages/PipelinesPage.test.tsx tests/acceptance/Pipelines.test.tsx
- docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml up -d --build --wait && docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml --profile e2e run --rm e2e pytest -q /workspace/tests/e2e/test_pipeline_graphs.py
max_attempts: 3
---

## Goal
Implement: PipelinesPage. The tests written by T-web-042t define done.

## Context
Stub `services/web/src/pages/PipelinesPage.tsx` (signature and props are final):
```tsx
/**
 * Route "/pipelines". listPipelineGraphs → left list grouped by stage ("chunk / semantic"), selected
 * graph rendered with <PipelineGraph>. Empty → "No pipeline graphs reported yet — is the worker
 * running?"
 */
export function PipelinesPage(): React.ReactElement {
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
