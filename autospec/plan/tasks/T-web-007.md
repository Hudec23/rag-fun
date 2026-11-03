---
id: T-web-007
kind: impl
feature: F-stage-flow
title: useArtifact hook
service: web
depends_on:
- T-web-007t
- T-web-002
edit:
- services/web/src/hooks/useArtifact.ts
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/hooks/useArtifact.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/hooks/useArtifact.ts && npx eslint src/hooks/useArtifact.ts'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/hooks/useArtifact.test.tsx
max_attempts: 3
---

## Goal
Implement: useArtifact hook. The tests written by T-web-007t define done.

## Context
Stub `services/web/src/hooks/useArtifact.ts` (signature and props are final):
```tsx
/** react-query ['artifact', stageRunId] via getArtifact<T>; disabled when stageRunId is null;
 * staleTime Infinity (artifacts never change). */
export function useArtifact<T>(_stageRunId: string | null): {
  data: T | undefined
  error: unknown
  isLoading: boolean
} {
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
