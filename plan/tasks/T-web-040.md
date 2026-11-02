---
id: T-web-040
kind: impl
feature: F-qdrant-browser
title: QdrantBrowserPage
service: web
depends_on:
- T-web-040t
- T-web-003
- T-web-013
- T-api-001
- T-api-002
- T-api-003
- T-api-004
- T-api-005
- T-api-008
- T-api-009
- T-api-010
- T-api-011
- T-api-012
- T-api-013
- T-api-014
- T-api-015
- T-api-016
- T-api-018
- T-api-019
- T-api-026
- T-api-027
- T-worker-005
- T-worker-006
- T-worker-007
- T-worker-008
- T-worker-009
- T-worker-012
- T-worker-017
- T-worker-022
- T-worker-025
- T-worker-027
- T-api-006
- T-api-007
- T-api-021
edit:
- services/web/src/pages/QdrantBrowserPage.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/pages/QdrantBrowserPage.test.tsx
- services/web/tests/acceptance/QdrantBrowser.test.tsx
- tests/e2e/test_qdrant_browser.py
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/pages/QdrantBrowserPage.tsx && npx eslint src/pages/QdrantBrowserPage.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/pages/QdrantBrowserPage.test.tsx tests/acceptance/QdrantBrowser.test.tsx
- docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml up -d --build --wait && docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml --profile e2e run --rm e2e pytest -q /workspace/tests/e2e/test_qdrant_browser.py
max_attempts: 3
---

## Goal
Implement: QdrantBrowserPage. The tests written by T-web-040t define done.

## Context
Stub `services/web/src/pages/QdrantBrowserPage.tsx` (signature and props are final):
```tsx
/**
 * Route "/qdrant/:collectionId?". Collection select (navigates). Info card from getQdrantInfo: exists,
 * status, points_count, vector config (shows the names text-dense / text-sparse, size, distance,
 * modifier), payload indexes table. <FilterBuilder> + matching count (countPoints). Points table
 * (scrollPoints limit 20, "Load more" with next_offset): point id (first 8), filename, page,
 * element_type, tags, content (80 chars). Click row → side panel with getPoint raw JSON (<pre>) showing
 * the first 16 dense dims + "… (<n> more)". exists false → "Nothing stored yet in this collection — run
 * the Store stage of an ingest run."
 */
export function QdrantBrowserPage(): React.ReactElement {
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
