---
id: T-web-004
kind: impl
feature: F-collections
title: api wrappers settings.ts + system.ts + collections create/delete
service: web
depends_on:
- T-web-004t
edit:
- services/web/src/api/settings.ts
- services/web/src/api/system.ts
- services/web/src/api/collections.ts
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/api/settingsSystem.test.ts
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/api/settings.ts src/api/system.ts src/api/collections.ts && npx eslint src/api/settings.ts src/api/system.ts src/api/collections.ts'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/api/settingsSystem.test.ts
max_attempts: 3
---

## Goal
Implement: api wrappers settings.ts + system.ts + collections create/delete. The tests written by T-web-004t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, src/api/schema.d.ts, package.json or package-lock.json.
- Do not add dependencies; Tailwind classes only for styling.
- Do not change exported names or props.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
