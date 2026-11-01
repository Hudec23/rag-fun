---
id: T-web-009
kind: impl
feature: F-stage-flow
title: ProgressBar
service: web
depends_on:
- T-web-009t
edit:
- services/web/src/components/ProgressBar.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/components/ProgressBar.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/components/ProgressBar.tsx && npx eslint src/components/ProgressBar.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/components/ProgressBar.test.tsx
max_attempts: 3
---

## Goal
Implement: ProgressBar. The tests written by T-web-009t define done.

## Context
Stub `services/web/src/components/ProgressBar.tsx` (signature and props are final):
```tsx
export interface ProgressBarProps {
  done: number
  total: number
  message?: string
}

/**
 * role="progressbar" with aria-valuenow=done, aria-valuemax=total, width % = round(done/total*100)
 * (0 when total ≤ 0, max 100). Shows "<done>/<total>" and message when given.
 */
export function ProgressBar(_props: ProgressBarProps): React.ReactElement {
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
