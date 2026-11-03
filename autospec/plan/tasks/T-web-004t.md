---
id: T-web-004t
kind: test
feature: F-collections
title: 'Write tests: api wrappers settings.ts + system.ts + collections create/delete'
service: web
depends_on: []
edit:
- services/web/tests/api/settingsSystem.test.ts
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/api/settingsSystem.test.ts && npx eslint tests/api/settingsSystem.test.ts && npx vitest list tests/api/settingsSystem.test.ts'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/api/settingsSystem.test.ts
max_attempts: 3
---

## Goal
Write unit tests for: api wrappers settings.ts + system.ts + collections create/delete. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-004 implements it.

## Context
Implement with `apiFetch` from src/api/client.ts (it prefixes /api/v1, sends JSON, throws ApiError). Paths and bodies: contracts/openapi/api.yaml.

Stub `services/web/src/api/settings.ts` (signature and props are final):
```tsx
import type { ModelCatalog, Settings, SettingsUpdate, TestConnectionResult } from './types'

export function getSettings(): Promise<Settings> {
  throw new Error('not implemented')
}

export function putSettings(_body: SettingsUpdate): Promise<Settings> {
  throw new Error('not implemented')
}

/** POST /settings/test-connection { target, override? }. */
export function testConnection(
  _target: 'ollama' | 'anthropic' | 'openai_compatible',
  _override?: { base_url: string | null; api_key: string | null },
): Promise<TestConnectionResult> {
  throw new Error('not implemented')
}

export function getModels(): Promise<ModelCatalog> {
  throw new Error('not implemented')
}
```

Stub `services/web/src/api/system.ts` (signature and props are final):
```tsx
import type { PipelineGraph, Status } from './types'

export function getStatus(): Promise<Status> {
  throw new Error('not implemented')
}

/** GET /pipeline-graphs → items. */
export function listPipelineGraphs(): Promise<PipelineGraph[]> {
  throw new Error('not implemented')
}

export function getPipelineGraph(_stage: string, _variant: string): Promise<PipelineGraph> {
  throw new Error('not implemented')
}
```

Stub `services/web/src/api/collections.ts` (signature and props are final):
```tsx
import { apiFetch } from './client'
import type { Collection, CollectionCreate, CollectionList } from './types'

export function listCollections(): Promise<CollectionList> {
  return apiFetch<CollectionList>('/collections')
}

/** POST /collections → 201 Collection. */
export function createCollection(_body: CollectionCreate): Promise<Collection> {
  throw new Error('not implemented')
}

/** DELETE /collections/{id} → 204. */
export function deleteCollection(_id: string): Promise<void> {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. getSettings → GET /api/v1/settings; putSettings(body) → PUT with the body
2. testConnection('ollama') → POST /settings/test-connection { target: 'ollama' } (no override key); with override → { target, override }
3. getModels → GET /models; getStatus → GET /status
4. listPipelineGraphs → GET /pipeline-graphs and resolves to the items array; getPipelineGraph('chunk', 'fixed') → /pipeline-graphs/chunk/fixed
5. createCollection(body) → POST /collections; deleteCollection(id) → DELETE /collections/{id} resolves undefined

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
