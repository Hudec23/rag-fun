---
id: T-web-020
kind: impl
feature: F-embed
title: TokenView
service: web
depends_on:
- T-web-020t
edit:
- services/web/src/viz/TokenView.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/viz/TokenView.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/viz/TokenView.tsx && npx eslint src/viz/TokenView.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/TokenView.test.tsx
max_attempts: 3
---

## Goal
Implement: TokenView. The tests written by T-web-020t define done.

## Context
Stub `services/web/src/viz/TokenView.tsx` (signature and props are final):
```tsx
export interface TokenViewProps {
  tokens: string[]
  tokenCount: number
  maxTokens: number
  overLimit: boolean
}

/**
 * Token pills in order (alternating two background colors, data-testid="token"), header
 * "<tokenCount> / <maxTokens> tokens", red badge "over limit — truncated by the model" when overLimit,
 * note "showing first <tokens.length>" when tokens.length < tokenCount.
 */
export function TokenView(_props: TokenViewProps): React.ReactElement {
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
