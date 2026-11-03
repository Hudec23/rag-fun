---
id: T-web-008t
kind: test
feature: F-upload
title: 'Write tests: TagEditor'
service: web
depends_on: []
edit:
- services/web/tests/components/TagEditor.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/components/TagEditor.test.tsx && npx eslint tests/components/TagEditor.test.tsx && npx vitest list tests/components/TagEditor.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/components/TagEditor.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: TagEditor. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-008 implements it.

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

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. renders chips for ['a', 'b'] with remove buttons 'remove a', 'remove b'; clicking 'remove a' → onChange(['b'])
2. type 'Finance' + Enter → onChange(['a', 'b', 'finance'])
3. type 'x,' (comma) → onChange with 'x' appended
4. type 'bad tag!' + Enter → shows 'invalid tag', onChange not called
5. duplicate 'a' → not added; 65-char tag → 'invalid tag'
6. 32 tags → input disabled

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
