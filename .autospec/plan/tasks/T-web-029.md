---
id: T-web-029
kind: impl
feature: F-parse
title: ParseView
service: web
depends_on:
- T-web-029t
- T-web-017
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
edit:
- services/web/src/components/stages/ParseView.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/stages/ParseView.test.tsx
- services/web/tests/acceptance/ParseView.test.tsx
- tests/e2e/test_parse.py
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/components/stages/ParseView.tsx && npx eslint src/components/stages/ParseView.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/stages/ParseView.test.tsx tests/acceptance/ParseView.test.tsx
- docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml up -d --build --wait && docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml --profile e2e run --rm e2e pytest -q /workspace/tests/e2e/test_parse.py
max_attempts: 3
---

## Goal
Implement: ParseView. The tests written by T-web-029t define done.

## Context
Fixtures from tests/setup/fixtures.ts; derive variants with spread, e.g. { ...CHUNK, strategy: 'semantic', semantic: {...} }.

Stub `services/web/src/components/stages/ParseView.tsx` (signature and props are final):
```tsx
import type { ParseArtifact } from '../../api/types'

export interface ParseViewProps {
  stageRunId: string
  artifact: ParseArtifact
}

/**
 * Left: page selector (pages[]) + <PageWithBoxes> using pageImageUrl(stageRunId, page). Right:
 * element list for the page (type badge in ELEMENT_COLORS, text); selecting an element in either place
 * selects it in both. Tables render as an HTML <table> from table.cells (header cells as <th>).
 * Header line: "<n> pages · <m> elements · <t> tables" + "OCR used" badge when ocr_used. Formats
 * without pages: just the element list.
 */
export function ParseView(_props: ParseViewProps): React.ReactElement {
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
