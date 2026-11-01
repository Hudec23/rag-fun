---
id: T-web-012
kind: impl
feature: F-stage-flow
title: ParamsForm
service: web
depends_on:
- T-web-012t
edit:
- services/web/src/components/ParamsForm.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/components/ParamsForm.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/components/ParamsForm.tsx && npx eslint src/components/ParamsForm.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/components/ParamsForm.test.tsx
max_attempts: 3
---

## Goal
Implement: ParamsForm. The tests written by T-web-012t define done.

## Context
Stub `services/web/src/components/ParamsForm.tsx` (signature and props are final):
```tsx
import type { Stage } from '../api/types'

export interface ParamsFormProps {
  stage: Stage
  value: Record<string, unknown>
  onChange: (v: Record<string, unknown>) => void
}

/**
 * Generic params editor for every stage (except retrieve filters, handled by FilterBuilder).
 * parse/chunk/transform: first a "Strategy" select (parse: docling_layout|docling_ocr|plain_text, chunk:
 * fixed|sentence|recursive|semantic|structure|table, transform: none|rewrite|multi_query|hyde); changing
 * it resets value to lib/defaults for that strategy. Then one labelled input per remaining field of the
 * current value: number → <input type="number"> (label = field name), boolean → checkbox, string enum
 * (split_by, mode) → select, string[] (separators) → comma-separated text input showing "\n" for
 * newlines. Emits a new object on every change (numbers parsed with Number()).
 */
export function ParamsForm(_props: ParamsFormProps): React.ReactElement {
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
