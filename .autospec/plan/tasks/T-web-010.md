---
id: T-web-010
kind: impl
feature: F-stage-flow
title: StageStepper
service: web
depends_on:
- T-web-010t
edit:
- services/web/src/components/StageStepper.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/components/StageStepper.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/components/StageStepper.tsx && npx eslint src/components/StageStepper.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/components/StageStepper.test.tsx
max_attempts: 3
---

## Goal
Implement: StageStepper. The tests written by T-web-010t define done.

## Context
Build StageRun values with stageRun() from tests/setup/fixtures.ts.

Stub `services/web/src/components/StageStepper.tsx` (signature and props are final):
```tsx
import type { StageRun } from '../api/types'

export interface StageStepperProps {
  stages: { name: string; run: StageRun | null }[]
  selected: string
  onSelect: (stage: string) => void
}

/**
 * Horizontal steps in the given order. Each step is a button with the stage name and a status badge:
 * "not run" when run is null, else run.status (+ " v<version>"). Badge colors: done green, failed red,
 * running/queued blue (with animate-pulse), stale amber. aria-current="step" on the selected one.
 */
export function StageStepper(_props: StageStepperProps): React.ReactElement {
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
