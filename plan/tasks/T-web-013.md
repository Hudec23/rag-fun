---
id: T-web-013
kind: impl
feature: F-qdrant-browser
title: FilterBuilder
service: web
depends_on:
- T-web-013t
- T-web-003
edit:
- services/web/src/components/FilterBuilder.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/components/FilterBuilder.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/components/FilterBuilder.tsx && npx eslint src/components/FilterBuilder.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/components/FilterBuilder.test.tsx
max_attempts: 3
---

## Goal
Implement: FilterBuilder. The tests written by T-web-013t define done.

## Context
Stub `services/web/src/components/FilterBuilder.tsx` (signature and props are final):
```tsx
import type { PayloadFilter } from '../api/types'

export interface FilterBuilderProps {
  collectionId: string
  value: PayloadFilter
  onChange: (f: PayloadFilter) => void
}

/**
 * Edits value.must only. Rows: key select (file_id, batch_id, tags, mime, element_type, chunk_strategy,
 * parse_strategy, page, chunk_index) + operator: keyword keys → "is any of" with a multi-select whose
 * options come from getFacet(collectionId, key) ("value (count)"); page/chunk_index → "between" with two
 * number inputs (gte/lte, empty = omitted). "Add condition" button appends {key: 'tags', match: {any: []}}
 * (not emitted until it has ≥1 value); "×" removes a row. Emits only complete conditions.
 */
export function FilterBuilder(_props: FilterBuilderProps): React.ReactElement {
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
