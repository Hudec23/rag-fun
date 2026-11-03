---
id: T-web-036
kind: impl
feature: F-generate
title: GenerateView
service: web
depends_on:
- T-web-036t
- T-web-026
- T-web-027
edit:
- services/web/src/components/stages/GenerateView.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/stages/GenerateView.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/components/stages/GenerateView.tsx && npx eslint src/components/stages/GenerateView.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/stages/GenerateView.test.tsx
max_attempts: 3
---

## Goal
Implement: GenerateView. The tests written by T-web-036t define done.

## Context
Fixtures from tests/setup/fixtures.ts; derive variants with spread, e.g. { ...CHUNK, strategy: 'semantic', semantic: {...} }.

Stub `services/web/src/components/stages/GenerateView.tsx` (signature and props are final):
```tsx
import type { GenerateArtifact } from '../../api/types'

export interface GenerateViewProps {
  stageRunId: string
  artifact: GenerateArtifact
  liveText?: string | null
}

/**
 * <TokenBudgetBar>, then <AnswerWithCitations answer context>; while props.liveText is set
 * (streaming) render that text instead with streaming=true. Collapsible "Prompt" with messages.
 * Footer: provider/model and usage tokens when not null.
 */
export function GenerateView(_props: GenerateViewProps): React.ReactElement {
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
