---
id: T-web-001
kind: impl
feature: F-upload
title: api wrappers batches.ts + files.ts
service: web
depends_on:
- T-web-001t
edit:
- services/web/src/api/batches.ts
- services/web/src/api/files.ts
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/api/batchesFiles.test.ts
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/api/batches.ts src/api/files.ts && npx eslint src/api/batches.ts src/api/files.ts'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/api/batchesFiles.test.ts
max_attempts: 3
---

## Goal
Implement: api wrappers batches.ts + files.ts. The tests written by T-web-001t define done.

## Context
Implement with `apiFetch` from src/api/client.ts (it prefixes /api/v1, sends JSON, throws ApiError). Paths and bodies: contracts/openapi/api.yaml.

Stub `services/web/src/api/batches.ts` (signature and props are final):
```tsx
import type { BatchList, BatchWithFiles, Batch, IngestParamsAll, IngestRun } from './types'

/** POST /batches multipart: one 'files' part per file, 'name' only when given, 'tags' = tags.join(',')
 * only when tags non-empty. → 201 BatchWithFiles. */
export function uploadBatch(
  _files: File[],
  _name: string | null,
  _tags: string[],
): Promise<BatchWithFiles> {
  throw new Error('not implemented')
}

/** GET /batches?limit=&offset= */
export function listBatches(_limit = 50, _offset = 0): Promise<BatchList> {
  throw new Error('not implemented')
}

export function getBatch(_id: string): Promise<BatchWithFiles> {
  throw new Error('not implemented')
}

/** PATCH /batches/{id} with only the given fields. */
export function updateBatch(
  _id: string,
  _patch: { name?: string; tags?: string[] },
): Promise<Batch> {
  throw new Error('not implemented')
}

/** POST /batches/{id}/ingest → 202 { items: IngestRun[] }. */
export function ingestBatch(
  _id: string,
  _collectionId: string,
  _params: IngestParamsAll,
): Promise<{ items: IngestRun[] }> {
  throw new Error('not implemented')
}
```

Stub `services/web/src/api/files.ts` (signature and props are final):
```tsx
import type { FileItem, FileList } from './types'
import { API_BASE } from './client'

/** GET /files with optional filters; omitted/undefined filters are not sent. */
export function listFiles(_q: {
  limit?: number
  offset?: number
  batch_id?: string
  tag?: string
  mime?: string
}): Promise<FileList> {
  throw new Error('not implemented')
}

export function getFile(_id: string): Promise<FileItem> {
  throw new Error('not implemented')
}

/** PATCH /files/{id} { tags }. */
export function updateFileTags(_id: string, _tags: string[]): Promise<FileItem> {
  throw new Error('not implemented')
}

export function deleteFile(_id: string): Promise<void> {
  throw new Error('not implemented')
}

export function fileContentUrl(id: string): string {
  return `${API_BASE}/files/${id}/content`
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
