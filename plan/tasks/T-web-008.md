---
id: T-web-008
kind: impl
feature: F-upload
title: TagEditor
service: web
depends_on:
- T-web-008t
edit:
- services/web/src/components/TagEditor.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/components/TagEditor.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/components/TagEditor.tsx && npx eslint src/components/TagEditor.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/components/TagEditor.test.tsx
max_attempts: 3
---

## Goal
Implement: TagEditor. The tests written by T-web-008t define done.

## Context
Stub `services/web/src/components/TagEditor.tsx` (signature and props are final):
```tsx
export interface TagEditorProps {
  tags: string[]
  onChange: (tags: string[]) => void
}

/**
 * Chips for each tag with a "×" button (aria-label "remove <tag>"). Text input (aria-label "Add tag"):
 * Enter or ',' adds the trimmed lowercased value if it matches /^[a-z0-9][a-z0-9_.:-]*$/, is ≤64 chars and
 * not a duplicate; otherwise shows "invalid tag" and does not call onChange. Max 32 tags (input disabled).
 */
export function TagEditor(_props: TagEditorProps): React.ReactElement {
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
