// F-settings (UI)
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'

import { SettingsPage } from '../../src/pages/SettingsPage'
import { renderWithProviders } from '../setup/render'
import { server } from '../setup/server'

const SETTINGS = {
  chat_provider: 'ollama',
  ollama: { url: 'http://host.docker.internal:11434', chat_model: 'qwen3:8b' },
  anthropic: { model: 'claude-sonnet-5-5', api_key_set: true, api_key_masked: 'sk-…abcd' },
  openai_compatible: { base_url: null, model: null, api_key_set: false, api_key_masked: null },
  reranker_model: 'Xenova/ms-marco-MiniLM-L-6-v2',
  updated_at: '2026-11-01T18:22:05.123Z',
}
const MODELS = {
  ollama_reachable: true,
  ollama_installed: ['qwen3:8b', 'bge-m3:latest'],
  dense: [
    { model: 'bge-m3', dims: 1024, max_tokens: 8192, installed: true },
    { model: 'nomic-embed-text', dims: 768, max_tokens: 8192, installed: false },
    { model: 'mxbai-embed-large', dims: 1024, max_tokens: 512, installed: false },
    { model: 'all-minilm', dims: 384, max_tokens: 256, installed: false },
  ],
  sparse: ['Qdrant/bm25', 'prithivida/Splade_PP_en_v1'],
  rerank: ['Xenova/ms-marco-MiniLM-L-6-v2', 'BAAI/bge-reranker-base'],
}

test('switch to anthropic keeping the stored key, and test a connection', async () => {
  let saved: Record<string, unknown> | null = null
  server.use(
    http.get('/api/v1/settings', () => HttpResponse.json(SETTINGS)),
    http.get('/api/v1/models', () => HttpResponse.json(MODELS)),
    http.put('/api/v1/settings', async ({ request }) => {
      saved = (await request.json()) as Record<string, unknown>
      return HttpResponse.json({ ...SETTINGS, chat_provider: 'anthropic' })
    }),
    http.post('/api/v1/settings/test-connection', () =>
      HttpResponse.json({
        target: 'ollama',
        ok: true,
        latency_ms: 12,
        detail: null,
        models: ['qwen3:8b', 'bge-m3:latest'],
      }),
    ),
  )
  const user = userEvent.setup()
  renderWithProviders(<SettingsPage />)
  expect(await screen.findByPlaceholderText('sk-…abcd')).toBeInTheDocument()
  expect(screen.getByText('ollama pull nomic-embed-text')).toBeInTheDocument()
  await user.click(screen.getAllByRole('button', { name: 'Test connection' })[0])
  expect(await screen.findByText('✓ 2 models, 12 ms')).toBeInTheDocument()
  await user.click(screen.getByRole('radio', { name: 'anthropic' }))
  await user.click(screen.getByRole('button', { name: 'Save' }))
  await waitFor(() => expect(saved).not.toBeNull())
  expect(saved!.chat_provider).toBe('anthropic')
  expect(saved!.anthropic).toEqual({ model: 'claude-sonnet-5-5', api_key: null })
})
