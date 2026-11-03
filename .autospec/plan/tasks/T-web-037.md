---
id: T-web-037
kind: impl
feature: F-stage-flow
title: StagePanel
service: web
depends_on:
- T-web-037t
- T-web-007
- T-web-009
- T-web-011
- T-web-012
edit:
- services/web/src/components/StagePanel.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/components/StagePanel.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/components/StagePanel.tsx && npx eslint src/components/StagePanel.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/components/StagePanel.test.tsx
max_attempts: 3
---

## Goal
Implement: StagePanel. The tests written by T-web-037t define done.

## Context
Stub `services/web/src/components/StagePanel.tsx` (signature and props are final):
```tsx
import type { Stage, StageRun } from '../api/types'

export interface StagePanelProps {
  runId: string
  runKind: 'ingest' | 'query'
  stage: Stage
  run: StageRun | null
  progress?: { done: number; total: number; message: string }
  liveText?: string | null
  extra?: Record<string, unknown>
}

/**
 * One stage of a run: <ParamsForm> initialised from run.params (or lib/defaults), "Run <stage>" button
 * → startIngestStage / startQueryStage (ApiError → ErrorBox, e.g. STAGE_PREREQUISITE_MISSING), status
 * line, <ProgressBar> while queued/running, error box when failed (error.code: error.message), stale
 * banner "Outdated — an earlier stage was re-run", <VersionPicker>; when the selected version is done:
 * useArtifact + the stage's <XView> (props from `extra`: collectionId, chunks). Retrieve stage also
 * shows <FilterBuilder> bound to params.filters (needs extra.collectionId).
 */
export function StagePanel(_props: StagePanelProps): React.ReactElement {
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
