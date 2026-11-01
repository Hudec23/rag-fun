---
id: T-web-016
kind: impl
feature: F-upload
title: UploadDropzone
service: web
depends_on:
- T-web-016t
- T-web-001
- T-web-008
edit:
- services/web/src/components/UploadDropzone.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/components/UploadDropzone.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/components/UploadDropzone.tsx && npx eslint src/components/UploadDropzone.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/components/UploadDropzone.test.tsx
max_attempts: 3
---

## Goal
Implement: UploadDropzone. The tests written by T-web-016t define done.

## Context
Stub `services/web/src/components/UploadDropzone.tsx` (signature and props are final):
```tsx
export interface UploadDropzoneProps {
  onUploaded: (batchId: string) => void
}

/**
 * Drop zone + hidden <input type="file" multiple aria-label="Choose files">. Selected files listed by
 * name. Optional batch name input (label "Batch name") and <TagEditor> for batch tags. Button
 * "Upload N files" (disabled with 0 files) → uploadBatch → onUploaded(batch.id), clear selection.
 * ApiError (e.g. UNSUPPORTED_FILE_TYPE) → <ErrorBox>, selection kept.
 */
export function UploadDropzone(_props: UploadDropzoneProps): React.ReactElement {
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
