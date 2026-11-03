---
id: T-web-037t
kind: test
feature: F-stage-flow
title: 'Write tests: StagePanel'
service: web
depends_on:
- T-web-002
edit:
- services/web/tests/components/StagePanel.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/components/StagePanel.test.tsx && npx eslint tests/components/StagePanel.test.tsx && npx vitest list tests/components/StagePanel.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/components/StagePanel.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: StagePanel. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-037 implements it.

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

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. run null (stage chunk) → ParamsForm with CHUNK_DEFAULTS.recursive, button 'Run chunk' → POST /ingest-runs/r/stages/chunk { params }
2. 409 response → alert 'STAGE_PREREQUISITE_MISSING: …'
3. run running + progress {1, 2, 'm'} → progressbar
4. run failed with error {code PARSE_FAILED} → 'PARSE_FAILED: …'
5. run stale → 'Outdated — an earlier stage was re-run'
6. run done → artifact fetched and the stage view rendered (vi.mock the view module to a stub that prints 'VIEW <stageRunId>')
7. stage retrieve → FilterBuilder rendered (vi.mock FilterBuilder)

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
