import { apiFetch } from './client'
import type { ModelCatalog, Settings, SettingsUpdate, TestConnectionResult } from './types'

export function getSettings(): Promise<Settings> {
  return apiFetch<Settings>('/settings')
}

export function putSettings(body: SettingsUpdate): Promise<Settings> {
  return apiFetch<Settings>('/settings', { method: 'PUT', body })
}

/** POST /settings/test-connection { target, override? }. */
export function testConnection(
  target: 'ollama' | 'anthropic' | 'openai_compatible',
  override?: { base_url: string | null; api_key: string | null },
): Promise<TestConnectionResult> {
  const body: {
    target: 'ollama' | 'anthropic' | 'openai_compatible'
    override?: { base_url: string | null; api_key: string | null }
  } = { target }
  if (override !== undefined) body.override = override
  return apiFetch<TestConnectionResult>('/settings/test-connection', { method: 'POST', body })
}

export function getModels(): Promise<ModelCatalog> {
  return apiFetch<ModelCatalog>('/models')
}
