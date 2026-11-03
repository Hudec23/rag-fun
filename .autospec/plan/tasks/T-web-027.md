---
id: T-web-027
kind: impl
feature: F-generate
title: AnswerWithCitations
service: web
depends_on:
- T-web-027t
edit:
- services/web/src/viz/AnswerWithCitations.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/viz/AnswerWithCitations.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/viz/AnswerWithCitations.tsx && npx eslint src/viz/AnswerWithCitations.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/AnswerWithCitations.test.tsx
max_attempts: 3
---

## Goal
Implement: AnswerWithCitations. The tests written by T-web-027t define done.

## Context
Stub `services/web/src/viz/AnswerWithCitations.tsx` (signature and props are final):
```tsx
import type { GenerateArtifact } from '../api/types'

export interface AnswerWithCitationsProps {
  answer: string
  context: GenerateArtifact['context']
  streaming?: boolean
}

/**
 * Answer text where every "[n]" / "[n, m]" marker becomes buttons "[n]" (one per number) that map to
 * context[n] (unknown n → plain text). Clicking a citation shows that chunk card (filename, page,
 * text) below and marks the button aria-pressed. streaming → blinking cursor after the text.
 * Below the answer: the context list numbered [1]..[k].
 */
export function AnswerWithCitations(_props: AnswerWithCitationsProps): React.ReactElement {
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
