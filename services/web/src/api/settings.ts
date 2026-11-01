import type { ModelCatalog, Settings, SettingsUpdate, TestConnectionResult } from './types'

export function getSettings(): Promise<Settings> {
  throw new Error('not implemented')
}

export function putSettings(_body: SettingsUpdate): Promise<Settings> {
  throw new Error('not implemented')
}

/** POST /settings/test-connection { target, override? }. */
export function testConnection(
  _target: 'ollama' | 'anthropic' | 'openai_compatible',
  _override?: { base_url: string | null; api_key: string | null },
): Promise<TestConnectionResult> {
  throw new Error('not implemented')
}

export function getModels(): Promise<ModelCatalog> {
  throw new Error('not implemented')
}
