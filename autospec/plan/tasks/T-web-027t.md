---
id: T-web-027t
kind: test
feature: F-generate
title: 'Write tests: AnswerWithCitations'
service: web
depends_on: []
edit:
- services/web/tests/viz/AnswerWithCitations.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/viz/AnswerWithCitations.test.tsx && npx eslint tests/viz/AnswerWithCitations.test.tsx && npx vitest list tests/viz/AnswerWithCitations.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/viz/AnswerWithCitations.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: AnswerWithCitations. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-027 implements it.

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

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. answer 'x [2] y [1, 2]' with 2 context items → buttons '[2]', '[1]', '[2]'
2. click '[1]' → aria-pressed true and the chunk card with its filename shown
3. unknown '[7]' stays plain text
4. streaming → an element with class animate-pulse after the text
5. context list numbered [1] and [2]

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
