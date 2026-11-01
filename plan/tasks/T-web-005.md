---
id: T-web-005
kind: impl
feature: F-live-progress
title: useRunEvents hook
service: web
depends_on:
- T-web-005t
edit:
- services/web/src/hooks/useRunEvents.ts
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/hooks/useRunEvents.test.ts
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/hooks/useRunEvents.ts && npx eslint src/hooks/useRunEvents.ts'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/hooks/useRunEvents.test.ts
max_attempts: 3
---

## Goal
Implement: useRunEvents hook. The tests written by T-web-005t define done.

## Context
Use renderHook from @testing-library/react. EventSource is globally replaced by MockEventSource (tests/setup/eventsource.ts).

Stub `services/web/src/hooks/useRunEvents.ts` (signature and props are final):
```tsx
import type { RunEvent } from '../api/types'

/** Opens EventSource(`${API_BASE}/events?run_id=${runId}`) while runId is non-null; for each of the
 * 6 event types (addEventListener per type) parses event.data as JSON and calls onEvent.
 * Closes on unmount or runId change. Malformed JSON is ignored. */
export function useRunEvents(_runId: string | null, _onEvent: (e: RunEvent) => void): void {
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
