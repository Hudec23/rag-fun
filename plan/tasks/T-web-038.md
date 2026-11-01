---
id: T-web-038
kind: impl
feature: F-upload
title: FilesPage
service: web
depends_on:
- T-web-038t
- T-web-001
- T-web-002
- T-web-008
- T-web-016
- T-api-001
- T-api-003
- T-api-008
- T-api-009
- T-api-010
- T-api-026
edit:
- services/web/src/pages/FilesPage.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/pages/FilesPage.test.tsx
- services/web/tests/acceptance/Upload.test.tsx
- tests/e2e/test_upload.py
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/pages/FilesPage.tsx && npx eslint src/pages/FilesPage.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/pages/FilesPage.test.tsx tests/acceptance/Upload.test.tsx
- docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml up -d --build --wait && docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml --profile e2e run --rm e2e pytest -q /workspace/tests/e2e/test_upload.py
max_attempts: 3
---

## Goal
Implement: FilesPage. The tests written by T-web-038t define done.

## Context
Stub `services/web/src/pages/FilesPage.tsx` (signature and props are final):
```tsx
/**
 * Route "/". <UploadDropzone> on top; then batches (listBatches) each with its files table: filename,
 * type, size (KB/MB, 1 decimal), tags (<TagEditor> → updateFileTags), actions "Ingest…" (collection
 * select + "Start" → createIngestRun then navigate to /ingest/<runId>) and "Delete" (confirm →
 * deleteFile). Batch row: name, tags editor (updateBatch), "Ingest batch" (collection select → ingestBatch
 * with INGEST_DEFAULTS, then shows "<n> runs started" with links).
 */
export function FilesPage(): React.ReactElement {
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
