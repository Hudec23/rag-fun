---
id: T-web-017
kind: impl
feature: F-parse
title: PageWithBoxes
service: web
depends_on:
- T-web-017t
edit:
- services/web/src/viz/PageWithBoxes.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/viz/PageWithBoxes.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/viz/PageWithBoxes.tsx && npx eslint src/viz/PageWithBoxes.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/PageWithBoxes.test.tsx
max_attempts: 3
---

## Goal
Implement: PageWithBoxes. The tests written by T-web-017t define done.

## Context
Stub `services/web/src/viz/PageWithBoxes.tsx` (signature and props are final):
```tsx
import type { ParseArtifact } from '../api/types'

export interface PageWithBoxesProps {
  imageUrl: string | null
  width: number
  height: number
  elements: ParseArtifact['elements']
  selectedId?: string | null
  onSelect?: (elementId: string) => void
}

/**
 * Page image (<img alt="page">) in a relative container; for every element with a bbox an absolutely
 * positioned <div data-testid="bbox" data-element-id=…> at left/top/width/height in % of the page
 * (l/width*100, t/height*100, (r-l)/width*100, (b-t)/height*100), border color ELEMENT_COLORS[type],
 * title = "<type>: <first 80 chars of text>". Click → onSelect(id). selectedId gets a thicker border.
 * imageUrl null → grey placeholder "No page image" with the boxes still drawn on a width:height box.
 * Legend below: one entry per element type present.
 */
export function PageWithBoxes(_props: PageWithBoxesProps): React.ReactElement {
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
