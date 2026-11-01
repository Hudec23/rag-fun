---
id: T-web-041t
kind: test
feature: F-settings
title: 'Write tests: SettingsPage'
service: web
depends_on:
- T-web-004
edit:
- services/web/tests/pages/SettingsPage.test.tsx
read:
- services/web/tests/pages/CollectionsPage.test.tsx
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check tests/pages/SettingsPage.test.tsx && npx eslint tests/pages/SettingsPage.test.tsx && npx vitest list tests/pages/SettingsPage.test.tsx'
expect_fail:
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/pages/SettingsPage.test.tsx
max_attempts: 3
---

## Goal
Write unit tests for: SettingsPage. Do not implement anything — the code under test is a stub that raises/throws 'not implemented'; task T-web-041 implements it.

## Context
Stub `services/web/src/pages/SettingsPage.tsx` (signature and props are final):
```tsx
/**
 * Route "/settings". Loads getSettings + getModels. Radio "Chat provider" (ollama | anthropic |
 * openai_compatible). Sections: Ollama (URL, chat model select from installed models or free text),
 * Anthropic (model, API key password input showing api_key_masked as placeholder, "Remove key"
 * checkbox → api_key ""), OpenAI-compatible (base URL, model, API key). Reranker model select.
 * "Test connection" per provider → testConnection(target, unsaved override) → "✓ <n> models, <ms> ms"
 * or "✗ <detail>". "Save" → putSettings (api_key null when the field was left empty). ApiError →
 * ErrorBox. Dense model table from getModels with installed ✓/✗ and hint `ollama pull <model>`.
 */
export function SettingsPage(): React.ReactElement {
  throw new Error('not implemented')
}
```

Test helpers: `renderWithProviders(ui, { path?, route? })` (tests/setup/render.tsx: fresh QueryClient without retries + MemoryRouter), msw `server.use(http.get('/api/v1/...', () => HttpResponse.json(...)))` (tests/setup/server.ts; unhandled requests fail the test), `MockEventSource.last().emit(type, data)` (tests/setup/eventsource.ts), Plotly is mocked: `<Plot>` renders `<div data-testid="plot" data-figure=JSON({data, layout})>`. Fixtures (tests/setup/fixtures.ts): COLLECTION, PARSE, CHUNK, EMBED, STORE, TRANSFORM, RETRIEVE, RERANK, GENERATE, GRAPH, RUN_ID, FILE_ID, `stageRun(stage, overrides)`. userEvent: `const user = userEvent.setup()`.

## Test cases
One test per case, named after the case. Follow the style of the example test file listed under `read:` (msw handlers per test, renderWithProviders, queries by role/label/text).
1. loads settings: radio 'ollama' checked, Ollama URL input value, Anthropic key placeholder 'sk-…abcd'
2. 'Remove key' checked + Save → anthropic.api_key ''
3. new key typed → api_key '<key>'; untouched → null
4. 'Test connection' for OpenAI-compatible sends override { base_url, api_key }; failure → '✗ <detail>'
5. dense table shows 'ollama pull all-minilm' for not installed models
6. 422 on save → alert with VALIDATION_ERROR

## Do not
- Do not write implementation code (not even to make a test compile).
- Do not use skip/xfail/todo, empty tests or always-true assertions.
- No real network, wall clock or unseeded randomness; only the fixtures/fakes named above (test infra containers postgres-test/redis-test/qdrant-test/s3-test are allowed where the context says so).

## Done when
`verify` passes (tests compile, are collected, lint clean) and `expect_fail` fails with every test red because of 'not implemented'.
