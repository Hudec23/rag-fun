---
id: T-web-014
kind: impl
feature: F-collections
title: CreateCollectionForm
service: web
depends_on:
- T-web-014t
- T-web-004
- T-api-011
- T-api-026
- T-worker-040t
- T-worker-040
edit:
- services/web/src/components/CreateCollectionForm.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/components/CreateCollectionForm.test.tsx
- services/web/tests/acceptance/Collections.test.tsx
- tests/e2e/test_collections.py
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/components/CreateCollectionForm.tsx && npx eslint src/components/CreateCollectionForm.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/components/CreateCollectionForm.test.tsx tests/acceptance/Collections.test.tsx
- docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml up -d --build --wait && docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml --profile e2e run --rm e2e pytest -q /workspace/tests/e2e/test_collections.py
max_attempts: 3
---

## Goal
Implement: CreateCollectionForm. The tests written by T-web-014t define done.

## Context
Stub `services/web/src/components/CreateCollectionForm.tsx` (signature and props are final):
```tsx
export interface CreateCollectionFormProps {
  onCreated?: () => void
}

/**
 * Inline form: name input (label "Name"), dense model select (label "Dense model", 4 options from
 * DenseModel), sparse model select (label "Sparse model"), button "Create". Submit → createCollection;
 * success → invalidate ['collections'], clear name, onCreated(); ApiError → <ErrorBox>. Button disabled
 * while name is empty or the request is pending.
 */
export function CreateCollectionForm(_props: CreateCollectionFormProps): React.ReactElement {
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
