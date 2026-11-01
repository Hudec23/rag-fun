---
id: T-web-002
kind: impl
feature: F-stage-flow
title: api wrappers runs.ts
service: web
depends_on:
- T-web-002t
edit:
- services/web/src/api/runs.ts
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/api/runs.test.ts
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/api/runs.ts && npx eslint src/api/runs.ts'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/api/runs.test.ts
max_attempts: 3
---

## Goal
Implement: api wrappers runs.ts. The tests written by T-web-002t define done.

## Context
Implement with `apiFetch` from src/api/client.ts (it prefixes /api/v1, sends JSON, throws ApiError). Paths and bodies: contracts/openapi/api.yaml.

Stub `services/web/src/api/runs.ts` (signature and props are final):
```tsx
import type {
  IngestParamsAll,
  IngestRun,
  IngestStage,
  QueryRun,
  QueryStage,
  Stage,
  StageRun,
  StageRunList,
} from './types'
import { API_BASE } from './client'

/** POST /ingest-runs → 201 IngestRun. */
export function createIngestRun(_fileId: string, _collectionId: string): Promise<IngestRun> {
  throw new Error('not implemented')
}

export function getIngestRun(_runId: string): Promise<IngestRun> {
  throw new Error('not implemented')
}

/** POST /ingest-runs/{runId}/stages/{stage} { params } → 202 StageRun. */
export function startIngestStage(
  _runId: string,
  _stage: IngestStage,
  _params: object,
): Promise<StageRun> {
  throw new Error('not implemented')
}

/** POST /ingest-runs/{runId}/run-all { from_stage, params } → IngestRun (200 or 202). */
export function runAllIngest(
  _runId: string,
  _fromStage: IngestStage | null,
  _params: IngestParamsAll,
): Promise<IngestRun> {
  throw new Error('not implemented')
}

/** POST /query-runs → 201 QueryRun. */
export function createQueryRun(_collectionId: string, _question: string): Promise<QueryRun> {
  throw new Error('not implemented')
}

export function getQueryRun(_runId: string): Promise<QueryRun> {
  throw new Error('not implemented')
}

/** POST /query-runs/{runId}/stages/{stage} { params } → 202 StageRun. */
export function startQueryStage(
  _runId: string,
  _stage: QueryStage,
  _params: object,
): Promise<StageRun> {
  throw new Error('not implemented')
}

/** GET /stage-runs?run_id=&stage= (all versions, newest first). */
export function listStageRuns(_runId: string, _stage: Stage): Promise<StageRunList> {
  throw new Error('not implemented')
}

/** GET /stage-runs/{id}/artifact. */
export function getArtifact<T>(_stageRunId: string): Promise<T> {
  throw new Error('not implemented')
}

export function pageImageUrl(stageRunId: string, pageNo: number): string {
  return `${API_BASE}/stage-runs/${stageRunId}/pages/${pageNo}`
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
