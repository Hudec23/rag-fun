// SettingsPage (F-settings): loads getSettings + getModels; provider radio group and per-provider
// sections; Test connection → "✓ <n> models, <ms> ms" / "✗ <detail>"; Save → putSettings
// (api_key null = keep stored key, '' = remove it); ApiError → ErrorBox; dense model table with
// "ollama pull <model>" hints for not installed models.
import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'

import { SettingsPage } from '../../src/pages/SettingsPage'
import type { SettingsUpdate } from '../../src/api/types'
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

test('loads settings', async () => {
  server.use(
    http.get('/api/v1/settings', () => HttpResponse.json(SETTINGS)),
    http.get('/api/v1/models', () => HttpResponse.json(MODELS)),
  )
  renderWithProviders(<SettingsPage />)
  expect(await screen.findByLabelText('URL')).toHaveValue('http://host.docker.internal:11434')
  expect(screen.getByRole('radio', { name: 'ollama' })).toBeChecked()
  expect(screen.getByPlaceholderText('sk-…abcd')).toBeInTheDocument()
})

test('checking "Remove key" and Save sends anthropic.api_key as an empty string', async () => {
  let saved: SettingsUpdate | null = null
  server.use(
    http.get('/api/v1/settings', () => HttpResponse.json(SETTINGS)),
    http.get('/api/v1/models', () => HttpResponse.json(MODELS)),
    http.put('/api/v1/settings', async ({ request }) => {
      saved = (await request.json()) as SettingsUpdate
      return HttpResponse.json(SETTINGS)
    }),
  )
  const user = userEvent.setup()
  renderWithProviders(<SettingsPage />)
  await user.click(await screen.findByLabelText('Remove key'))
  await user.click(screen.getByRole('button', { name: 'Save' }))
  await waitFor(() => expect(saved).not.toBeNull())
  expect(saved!.anthropic).toEqual({ model: 'claude-sonnet-5-5', api_key: '' })
})

test('a typed Anthropic key is sent as api_key, an untouched key sends api_key null', async () => {
  const saved: SettingsUpdate[] = []
  server.use(
    http.get('/api/v1/settings', () => HttpResponse.json(SETTINGS)),
    http.get('/api/v1/models', () => HttpResponse.json(MODELS)),
    http.put('/api/v1/settings', async ({ request }) => {
      saved.push((await request.json()) as SettingsUpdate)
      return HttpResponse.json(SETTINGS)
    }),
  )
  const user = userEvent.setup()
  const first = renderWithProviders(<SettingsPage />)
  await user.type(await screen.findByPlaceholderText('sk-…abcd'), 'sk-newkey-012345')
  await user.click(screen.getByRole('button', { name: 'Save' }))
  await waitFor(() => expect(saved).toHaveLength(1))
  expect(saved[0].anthropic).toEqual({ model: 'claude-sonnet-5-5', api_key: 'sk-newkey-012345' })
  first.unmount()

  renderWithProviders(<SettingsPage />)
  await user.click(await screen.findByRole('button', { name: 'Save' }))
  await waitFor(() => expect(saved).toHaveLength(2))
  expect(saved[1].anthropic).toEqual({ model: 'claude-sonnet-5-5', api_key: null })
})

test('OpenAI-compatible Test connection sends the unsaved override and shows the failure detail', async () => {
  let sent: {
    target: string
    override?: { base_url: string | null; api_key: string | null }
  } | null = null
  server.use(
    http.get('/api/v1/settings', () => HttpResponse.json(SETTINGS)),
    http.get('/api/v1/models', () => HttpResponse.json(MODELS)),
    http.post('/api/v1/settings/test-connection', async ({ request }) => {
      sent = (await request.json()) as typeof sent
      return HttpResponse.json({
        target: 'openai_compatible',
        ok: false,
        latency_ms: 15,
        detail: 'connection refused',
        models: [],
      })
    }),
  )
  const user = userEvent.setup()
  renderWithProviders(<SettingsPage />)
  await user.type(await screen.findByLabelText('Base URL'), 'http://host.docker.internal:1234/v1')
  const openai = screen.getByRole('group', { name: 'OpenAI-compatible' })
  await user.type(within(openai).getByLabelText('API key'), 'sk-test-987654')
  await user.click(screen.getAllByRole('button', { name: 'Test connection' })[2])
  await waitFor(() => expect(sent).not.toBeNull())
  expect(sent).toEqual({
    target: 'openai_compatible',
    override: { base_url: 'http://host.docker.internal:1234/v1', api_key: 'sk-test-987654' },
  })
  expect(await screen.findByText('✗ connection refused')).toBeInTheDocument()
})

test('the dense model table shows an ollama pull hint for not installed models', async () => {
  server.use(
    http.get('/api/v1/settings', () => HttpResponse.json(SETTINGS)),
    http.get('/api/v1/models', () => HttpResponse.json(MODELS)),
  )
  renderWithProviders(<SettingsPage />)
  expect(await screen.findByText('ollama pull all-minilm')).toBeInTheDocument()
  expect(screen.getByText('ollama pull nomic-embed-text')).toBeInTheDocument()
  expect(screen.getByText('ollama pull mxbai-embed-large')).toBeInTheDocument()
  expect(screen.queryByText('ollama pull bge-m3')).toBeNull()
})

test('a 422 on Save shows the VALIDATION_ERROR alert', async () => {
  server.use(
    http.get('/api/v1/settings', () => HttpResponse.json(SETTINGS)),
    http.get('/api/v1/models', () => HttpResponse.json(MODELS)),
    http.put('/api/v1/settings', () =>
      HttpResponse.json(
        {
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Request body or parameters are invalid',
            details: { field: 'openai_compatible.base_url' },
          },
        },
        { status: 422 },
      ),
    ),
  )
  const user = userEvent.setup()
  renderWithProviders(<SettingsPage />)
  await user.click(await screen.findByRole('radio', { name: 'openai_compatible' }))
  await user.click(screen.getByRole('button', { name: 'Save' }))
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'VALIDATION_ERROR: Request body or parameters are invalid',
  )
})
