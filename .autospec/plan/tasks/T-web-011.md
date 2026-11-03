---
id: T-web-011
kind: impl
feature: F-stage-flow
title: VersionPicker
service: web
depends_on:
- T-web-011t
- T-web-002
edit:
- services/web/src/components/VersionPicker.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/components/VersionPicker.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/components/VersionPicker.tsx && npx eslint src/components/VersionPicker.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/components/VersionPicker.test.tsx
max_attempts: 3
---

## Goal
Implement: VersionPicker. The tests written by T-web-011t define done.

## Context
Stub `services/web/src/components/VersionPicker.tsx` (signature and props are final):
```tsx
import type { Stage } from '../api/types'

export interface VersionPickerProps {
  runId: string
  stage: Stage
  selectedId: string | null
  onSelect: (stageRunId: string) => void
}

/**
 * <select aria-label="Version"> listing listStageRuns(runId, stage) items as "v<version> · <status>",
 * newest first; value = selectedId; change → onSelect(id). Hidden when there are < 2 versions.
 */
export function VersionPicker(_props: VersionPickerProps): React.ReactElement {
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
