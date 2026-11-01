---
id: T-web-015
kind: impl
feature: F-status
title: StatusBar
service: web
depends_on:
- T-web-015t
- T-web-004
- T-api-003
- T-api-023
- T-api-024
- T-api-026
- T-worker-010
edit:
- services/web/src/components/StatusBar.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/components/StatusBar.test.tsx
- services/web/tests/acceptance/StatusBar.test.tsx
- tests/e2e/test_status.py
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/components/StatusBar.tsx && npx eslint src/components/StatusBar.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/components/StatusBar.test.tsx tests/acceptance/StatusBar.test.tsx
- docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml up -d --build --wait && docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml --profile e2e run --rm e2e pytest -q /workspace/tests/e2e/test_status.py
max_attempts: 3
---

## Goal
Implement: StatusBar. The tests written by T-web-015t define done.

## Context
Stub `services/web/src/components/StatusBar.tsx` (signature and props are final):
```tsx
/**
 * Polls getStatus every 5 s (react-query refetchInterval). Renders one pill per component in response
 * order: text = component name, data-ok="true|false", green when ok, red when not with title = detail.
 * While loading: "Checking services…". Request error: one red pill "api" with the error message.
 */
export function StatusBar(): React.ReactElement {
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
