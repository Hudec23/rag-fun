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
import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import { getModels, getSettings, putSettings, testConnection } from '../api/settings'
import type { Settings, SettingsUpdate, TestConnectionResult } from '../api/types'
import { ErrorBox } from '../components/ErrorBox'

type Provider = SettingsUpdate['chat_provider']
type Reranker = Settings['reranker_model']

type Form = {
  chatProvider: Provider
  ollamaUrl: string
  chatModel: string
  anthropicModel: string
  anthropicKey: string
  anthropicRemoveKey: boolean
  openaiBaseUrl: string
  openaiModel: string
  openaiKey: string
  rerankerModel: Reranker
}

type Edits = Partial<Form>
type Probes = Partial<Record<Provider, TestConnectionResult>>

const PROVIDERS: readonly Provider[] = ['ollama', 'anthropic', 'openai_compatible']

const ROW_CLASS = 'flex items-center gap-2 text-sm'
const FIELD_CLASS = 'w-24 text-gray-700'
const CONTROL_CLASS = 'rounded border border-gray-300 bg-white px-2 py-1 text-sm'

function anthropicApiKey(form: Form): string | null {
  if (form.anthropicRemoveKey) return ''
  return form.anthropicKey !== '' ? form.anthropicKey : null
}

function buildUpdate(form: Form): SettingsUpdate {
  return {
    chat_provider: form.chatProvider,
    ollama: { url: form.ollamaUrl, chat_model: form.chatModel },
    anthropic: { model: form.anthropicModel, api_key: anthropicApiKey(form) },
    openai_compatible: {
      base_url: form.openaiBaseUrl !== '' ? form.openaiBaseUrl : null,
      model: form.openaiModel !== '' ? form.openaiModel : null,
      api_key: form.openaiKey !== '' ? form.openaiKey : null,
    },
    reranker_model: form.rerankerModel,
  }
}

function overrideFor(
  target: Provider,
  form: Form,
): { base_url: string | null; api_key: string | null } {
  if (target === 'ollama') {
    return { base_url: form.ollamaUrl !== '' ? form.ollamaUrl : null, api_key: null }
  }
  if (target === 'anthropic') {
    return { base_url: null, api_key: anthropicApiKey(form) }
  }
  return {
    base_url: form.openaiBaseUrl !== '' ? form.openaiBaseUrl : null,
    api_key: form.openaiKey !== '' ? form.openaiKey : null,
  }
}

function probeText(result: TestConnectionResult): string {
  return result.ok
    ? `✓ ${result.models.length} models, ${result.latency_ms} ms`
    : `✗ ${result.detail ?? 'unknown error'}`
}

export function SettingsPage(): React.ReactElement {
  const settingsQ = useQuery({ queryKey: ['settings'], queryFn: getSettings })
  const modelsQ = useQuery({ queryKey: ['models'], queryFn: getModels })
  const [edits, setEdits] = useState<Edits>({})
  const [error, setError] = useState<unknown>(null)
  const [probes, setProbes] = useState<Probes>({})
  const [probing, setProbing] = useState<Provider | null>(null)

  const saveMutation = useMutation({
    mutationFn: (body: SettingsUpdate) => putSettings(body),
    onSuccess: () => setError(null),
    onError: (err) => setError(err),
  })

  const queryError = settingsQ.error ?? modelsQ.error
  if (queryError) {
    return <ErrorBox error={queryError} />
  }
  if (settingsQ.isPending || modelsQ.isPending) {
    return <p className="p-4 text-sm text-gray-500">Loading…</p>
  }
  const settings = settingsQ.data!
  const models = modelsQ.data!

  // Field values = stored settings, overridden by local edits while unsaved.
  const form: Form = {
    chatProvider: edits.chatProvider ?? settings.chat_provider,
    ollamaUrl: edits.ollamaUrl ?? settings.ollama.url,
    chatModel: edits.chatModel ?? settings.ollama.chat_model,
    anthropicModel: edits.anthropicModel ?? settings.anthropic.model,
    anthropicKey: edits.anthropicKey ?? '',
    anthropicRemoveKey: edits.anthropicRemoveKey ?? false,
    openaiBaseUrl: edits.openaiBaseUrl ?? settings.openai_compatible.base_url ?? '',
    openaiModel: edits.openaiModel ?? settings.openai_compatible.model ?? '',
    openaiKey: edits.openaiKey ?? '',
    rerankerModel: edits.rerankerModel ?? settings.reranker_model,
  }

  const update = <K extends keyof Edits>(key: K, value: Edits[K]) =>
    setEdits((e) => ({ ...e, [key]: value }))

  const runProbe = (target: Provider) => {
    if (probing !== null) return
    setError(null)
    setProbing(target)
    testConnection(target, overrideFor(target, form))
      .then((result) => setProbes((p) => ({ ...p, [target]: result })))
      .catch((err: unknown) => setError(err))
      .finally(() => setProbing(null))
  }

  const probeResultText = (target: Provider): string | null => {
    const result = probes[target]
    return result !== undefined ? probeText(result) : null
  }

  const chatModelOptions = models.ollama_installed.includes(form.chatModel)
    ? models.ollama_installed
    : [form.chatModel, ...models.ollama_installed]
  const rerankOptions = models.rerank.includes(form.rerankerModel)
    ? models.rerank
    : [form.rerankerModel, ...models.rerank]

  const providerSection = (target: Provider, label: string, content: React.ReactNode) => (
    <section role="group" aria-label={label} className="mb-3 rounded border bg-white p-3">
      <h2 className="mb-2 text-sm font-semibold">{label}</h2>
      {content}
      <div className="mt-2 flex flex-wrap items-center gap-3">
        <button
          type="button"
          disabled={probing !== null}
          className={CONTROL_CLASS}
          onClick={() => runProbe(target)}
        >
          Test connection
        </button>
        {probeResultText(target)}
      </div>
    </section>
  )

  return (
    <section className="p-4">
      <h1 className="mb-3 text-lg font-semibold">Settings</h1>

      <fieldset className="mb-3 rounded border p-3">
        <legend className="px-1 text-sm font-semibold">Chat provider</legend>
        <div className="flex flex-wrap gap-3">
          {PROVIDERS.map((p) => (
            <label key={p} className="flex items-center gap-1 text-sm">
              <input
                type="radio"
                name="chat_provider"
                value={p}
                checked={form.chatProvider === p}
                onChange={() => update('chatProvider', p)}
              />
              {p}
            </label>
          ))}
        </div>
      </fieldset>

      {providerSection(
        'ollama',
        'Ollama',
        <div className="space-y-2">
          <label className={ROW_CLASS}>
            <span className={FIELD_CLASS}>URL</span>
            <input
              type="text"
              className={CONTROL_CLASS}
              value={form.ollamaUrl}
              onChange={(event) => update('ollamaUrl', event.target.value)}
            />
          </label>
          <label className={ROW_CLASS}>
            <span className={FIELD_CLASS}>Chat model</span>
            <select
              className={CONTROL_CLASS}
              value={form.chatModel}
              onChange={(event) => update('chatModel', event.target.value)}
            >
              {chatModelOptions.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </label>
        </div>,
      )}

      {providerSection(
        'anthropic',
        'Anthropic',
        <div className="space-y-2">
          <label className={ROW_CLASS}>
            <span className={FIELD_CLASS}>Model</span>
            <input
              type="text"
              className={CONTROL_CLASS}
              value={form.anthropicModel}
              onChange={(event) => update('anthropicModel', event.target.value)}
            />
          </label>
          <label className={ROW_CLASS}>
            <span className={FIELD_CLASS}>API key</span>
            <input
              type="password"
              className={CONTROL_CLASS}
              placeholder={settings.anthropic.api_key_masked ?? undefined}
              value={form.anthropicKey}
              disabled={form.anthropicRemoveKey}
              onChange={(event) => update('anthropicKey', event.target.value)}
            />
          </label>
          <label className={ROW_CLASS}>
            <input
              type="checkbox"
              checked={form.anthropicRemoveKey}
              onChange={(event) => update('anthropicRemoveKey', event.target.checked)}
            />
            <span>Remove key</span>
          </label>
        </div>,
      )}

      {providerSection(
        'openai_compatible',
        'OpenAI-compatible',
        <div className="space-y-2">
          <label className={ROW_CLASS}>
            <span className={FIELD_CLASS}>Base URL</span>
            <input
              type="text"
              className={CONTROL_CLASS}
              value={form.openaiBaseUrl}
              onChange={(event) => update('openaiBaseUrl', event.target.value)}
            />
          </label>
          <label className={ROW_CLASS}>
            <span className={FIELD_CLASS}>Model</span>
            <input
              type="text"
              className={CONTROL_CLASS}
              value={form.openaiModel}
              onChange={(event) => update('openaiModel', event.target.value)}
            />
          </label>
          <label className={ROW_CLASS}>
            <span className={FIELD_CLASS}>API key</span>
            <input
              type="password"
              className={CONTROL_CLASS}
              placeholder={settings.openai_compatible.api_key_masked ?? undefined}
              value={form.openaiKey}
              onChange={(event) => update('openaiKey', event.target.value)}
            />
          </label>
        </div>,
      )}

      <label className="mb-3 flex w-fit items-center gap-2 text-sm">
        <span className={FIELD_CLASS}>Reranker model</span>
        <select
          className={CONTROL_CLASS}
          value={form.rerankerModel}
          onChange={(event) => update('rerankerModel', event.target.value as Reranker)}
        >
          {rerankOptions.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </label>

      <div className="mb-3">
        <button
          type="button"
          disabled={saveMutation.isPending}
          className={CONTROL_CLASS}
          onClick={() => saveMutation.mutate(buildUpdate(form))}
        >
          Save
        </button>
      </div>

      {error !== null ? <ErrorBox error={error} /> : null}

      <h2 className="mb-2 mt-4 text-sm font-semibold">Models</h2>
      <table className="w-full border-collapse bg-white text-sm">
        <thead>
          <tr className="text-left text-xs uppercase text-gray-500">
            <th className="border-b px-2 py-1">Model</th>
            <th className="border-b px-2 py-1">Dims</th>
            <th className="border-b px-2 py-1">Max tokens</th>
            <th className="border-b px-2 py-1">Installed</th>
          </tr>
        </thead>
        <tbody>
          {models.dense.map((m) => (
            <tr key={m.model} className="border-b">
              <td className="px-2 py-1">{m.model}</td>
              <td className="px-2 py-1">{m.dims}</td>
              <td className="px-2 py-1">{m.max_tokens}</td>
              <td className="px-2 py-1">
                {m.installed ? '✓' : '✗'}
                {m.installed ? null : (
                  <code className="ml-2 rounded bg-gray-100 px-1 text-xs">
                    ollama pull {m.model}
                  </code>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
