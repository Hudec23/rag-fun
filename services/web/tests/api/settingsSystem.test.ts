// API wrapper tests for src/api/settings.ts + system.ts + collections.ts (create/delete): each test
// registers an msw handler that captures the request and asserts the exact method, path and body sent.
import { http, HttpResponse } from 'msw'

import { createCollection, deleteCollection } from '../../src/api/collections'
import { getModels, getSettings, putSettings, testConnection } from '../../src/api/settings'
import { getPipelineGraph, getStatus, listPipelineGraphs } from '../../src/api/system'
import type {
  CollectionCreate,
  ModelCatalog,
  Settings,
  SettingsUpdate,
  Status,
  TestConnectionResult,
} from '../../src/api/types'
import { COLLECTION, GRAPH } from '../setup/fixtures'
import { server } from '../setup/server'

const SETTINGS: Settings = {
  chat_provider: 'anthropic',
  ollama: { url: 'http://host.docker.internal:11434', chat_model: 'qwen3:8b' },
  anthropic: {
    model: 'claude-sonnet-5-5',
    api_key_set: true,
    api_key_masked: 'sk-…mple',
  },
  openai_compatible: {
    base_url: 'http://host.docker.internal:1234/v1',
    model: 'local-model',
    api_key_set: false,
    api_key_masked: null,
  },
  reranker_model: 'Xenova/ms-marco-MiniLM-L-6-v2',
  updated_at: '2026-11-01T18:22:05.123Z',
}
const SETTINGS_UPDATE: SettingsUpdate = {
  chat_provider: 'anthropic',
  ollama: { url: 'http://host.docker.internal:11434', chat_model: 'qwen3:8b' },
  anthropic: { model: 'claude-sonnet-5-5', api_key: 'sk-ant-example' },
  openai_compatible: {
    base_url: 'http://host.docker.internal:1234/v1',
    model: 'local-model',
    api_key: null,
  },
  reranker_model: 'Xenova/ms-marco-MiniLM-L-6-v2',
}
const TEST_CONNECTION: TestConnectionResult = {
  target: 'ollama',
  ok: true,
  latency_ms: 12,
  detail: null,
  models: ['qwen3:8b', 'bge-m3:latest'],
}
const MODEL_CATALOG: ModelCatalog = {
  ollama_reachable: true,
  ollama_installed: ['bge-m3:latest', 'qwen3:8b'],
  dense: [
    { model: 'bge-m3', dims: 1024, max_tokens: 8192, installed: true },
    { model: 'nomic-embed-text', dims: 768, max_tokens: 8192, installed: false },
  ],
  sparse: ['Qdrant/bm25'],
  rerank: ['Xenova/ms-marco-MiniLM-L-6-v2'],
}
const STATUS: Status = {
  components: [
    { name: 'api', ok: true, latency_ms: 2, detail: null },
    { name: 'postgres', ok: true, latency_ms: 1, detail: null },
    { name: 'ollama', ok: false, latency_ms: 5000, detail: 'connect ECONNREFUSED' },
  ],
}
const COLLECTION_CREATE: CollectionCreate = {
  name: 'experiments',
  dense_model: 'nomic-embed-text',
  sparse_model: 'prithivida/Splade_PP_en_v1',
}

test('getSettings gets /settings; putSettings puts the update body', async () => {
  let body: unknown = null
  server.use(
    http.get('/api/v1/settings', () => HttpResponse.json(SETTINGS)),
    http.put('/api/v1/settings', async ({ request }) => {
      body = await request.json()
      return HttpResponse.json(SETTINGS)
    }),
  )
  const settings = await getSettings()
  expect(settings).toEqual(SETTINGS)
  const saved = await putSettings(SETTINGS_UPDATE)
  expect(saved).toEqual(SETTINGS)
  expect(body).toEqual(SETTINGS_UPDATE)
})

test('testConnection posts { target } without an override key, or { target, override }', async () => {
  let body: unknown = null
  server.use(
    http.post('/api/v1/settings/test-connection', async ({ request }) => {
      body = await request.json()
      return HttpResponse.json(TEST_CONNECTION)
    }),
  )
  const plain = await testConnection('ollama')
  expect(plain).toEqual(TEST_CONNECTION)
  expect(body).toEqual({ target: 'ollama' })
  expect(body).not.toHaveProperty('override')
  const overridden = await testConnection('openai_compatible', {
    base_url: 'http://host.docker.internal:1234/v1',
    api_key: 'sk-ant-override',
  })
  expect(overridden).toEqual(TEST_CONNECTION)
  expect(body).toEqual({
    target: 'openai_compatible',
    override: { base_url: 'http://host.docker.internal:1234/v1', api_key: 'sk-ant-override' },
  })
})

test('getModels gets /models; getStatus gets /status', async () => {
  server.use(
    http.get('/api/v1/models', () => HttpResponse.json(MODEL_CATALOG)),
    http.get('/api/v1/status', () => HttpResponse.json(STATUS)),
  )
  const models = await getModels()
  expect(models).toEqual(MODEL_CATALOG)
  const status = await getStatus()
  expect(status).toEqual(STATUS)
})

test('listPipelineGraphs gets /pipeline-graphs items; getPipelineGraph gets the stage/variant path', async () => {
  server.use(
    http.get('/api/v1/pipeline-graphs', () => HttpResponse.json({ items: [GRAPH] })),
    http.get('/api/v1/pipeline-graphs/chunk/fixed', () => HttpResponse.json(GRAPH)),
  )
  const graphs = await listPipelineGraphs()
  expect(graphs).toEqual([GRAPH])
  const graph = await getPipelineGraph('chunk', 'fixed')
  expect(graph).toEqual(GRAPH)
})

test('createCollection posts /collections; deleteCollection deletes /collections/{id}', async () => {
  let body: unknown = null
  server.use(
    http.post('/api/v1/collections', async ({ request }) => {
      body = await request.json()
      return HttpResponse.json(COLLECTION, { status: 201 })
    }),
    http.delete(
      `/api/v1/collections/${COLLECTION.id}`,
      () => new HttpResponse(null, { status: 204 }),
    ),
  )
  const created = await createCollection(COLLECTION_CREATE)
  expect(created).toEqual(COLLECTION)
  expect(body).toEqual(COLLECTION_CREATE)
  expect(await deleteCollection(COLLECTION.id)).toBeUndefined()
})
