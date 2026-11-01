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
