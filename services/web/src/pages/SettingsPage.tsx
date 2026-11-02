/**
 * Route "/settings". Loads getSettings + getModels. Radio group "Chat provider": three
 * <input type="radio"> whose labels are exactly "ollama", "anthropic", "openai_compatible". Sections:
 * Ollama (URL, chat model select from installed models or free text), Anthropic (model, API key password
 * input with placeholder = api_key_masked, "Remove key" checkbox → api_key ""), OpenAI-compatible (base
 * URL, model, API key). Reranker model select. One "Test connection" button per provider section, in
 * order ollama, anthropic, openai_compatible → testConnection(target, unsaved override) → "✓ <n> models,
 * <ms> ms" or "✗ <detail>". "Save" → putSettings (api_key null when the field was left empty). ApiError
 * → ErrorBox. Dense model table from getModels with installed ✓/✗ and hint `ollama pull <model>` for
 * models not installed.
 */
export function SettingsPage(): React.ReactElement {
  throw new Error('not implemented')
}
