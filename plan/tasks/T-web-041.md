---
id: T-web-041
kind: impl
feature: F-settings
title: SettingsPage
service: web
depends_on:
- T-web-041t
- T-web-004
- T-api-012
- T-api-022
- T-api-026
edit:
- services/web/src/pages/SettingsPage.tsx
read:
- services/web/src/pages/CollectionsPage.tsx
locked:
- services/web/tests/pages/SettingsPage.test.tsx
- services/web/tests/acceptance/Settings.test.tsx
- tests/e2e/test_settings.py
verify:
- docker compose -f docker-compose.dev.yml run --rm web-dev sh -c 'npx tsc -b && npx prettier --check src/pages/SettingsPage.tsx && npx eslint src/pages/SettingsPage.tsx'
- docker compose -f docker-compose.dev.yml run --rm web-dev npx vitest run tests/pages/SettingsPage.test.tsx tests/acceptance/Settings.test.tsx
- docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml up -d --build --wait && docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml --profile e2e run --rm e2e pytest -q /workspace/tests/e2e/test_settings.py
max_attempts: 3
---

## Goal
Implement: SettingsPage. The tests written by T-web-041t define done.

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

## Steps
1. Implement every stub listed in Context exactly as its docstring says.
2. Run the verify commands; fix until green.

## Do not
- Do not edit any test file, src/api/schema.d.ts, package.json or package-lock.json.
- Do not add dependencies; Tailwind classes only for styling.
- Do not change exported names or props.

## Done when
All verify commands pass and the service regression still passes. Red tests of unfinished tasks are expected — ignore them.
