// API wrapper tests for src/api/runs.ts: each test registers an msw handler that captures the
// request and asserts the exact method, path, query params and body sent.
import { http, HttpResponse } from 'msw'

import { ApiError } from '../../src/api/client'
import {
  createIngestRun,
  createQueryRun,
  getArtifact,
  listStageRuns,
  pageImageUrl,
  runAllIngest,
  runAllQuery,
  startIngestStage,
  startQueryStage,
} from '../../src/api/runs'
import type {
  ChunkArtifact,
  FileItem,
  GenerateParams,
  IngestParamsAll,
  IngestRun,
  QueryRun,
  RerankParams,
  RetrieveParams,
  TransformParams,
} from '../../src/api/types'
import { CHUNK, COLLECTION, FILE_ID, RUN_ID, stageRun } from '../setup/fixtures'
import { server } from '../setup/server'

const CREATED_AT = '2026-11-01T18:22:05.123Z'
const QUERY_RUN_ID = '019a4b2c-2000-7c00-9000-000000000004'

const FILE: FileItem = {
  id: FILE_ID,
  batch_id: '019a4b2c-1e00-7b00-8000-000000000001',
  filename: 'q3-report.pdf',
  mime: 'application/pdf',
  size_bytes: 482113,
  sha256: 'a'.repeat(64),
  tags: [],
  created_at: CREATED_AT,
}
const INGEST_RUN: IngestRun = {
  id: RUN_ID,
  file: FILE,
  collection_id: COLLECTION.id,
  created_at: CREATED_AT,
  run_all_pending: [],
  stages: {
    parse: stageRun('parse'),
    chunk: stageRun('chunk'),
    embed: stageRun('embed'),
    store: stageRun('store'),
  },
}
const QUERY_RUN: QueryRun = {
  id: QUERY_RUN_ID,
  collection_id: COLLECTION.id,
  question: 'q?',
  created_at: CREATED_AT,
  run_all_pending: [],
  stages: {
    transform: stageRun('transform', { run_id: QUERY_RUN_ID }),
    retrieve: stageRun('retrieve', { run_id: QUERY_RUN_ID }),
    rerank: stageRun('rerank', { run_id: QUERY_RUN_ID }),
    generate: stageRun('generate', { run_id: QUERY_RUN_ID }),
  },
}
const INGEST_PARAMS: IngestParamsAll = {
  parse: { strategy: 'docling_layout', extract_tables: true, page_images: true },
  chunk: { strategy: 'fixed', split_by: 'word', length: 200, overlap: 20 },
  embed: { batch_size: 16 },
  store: {},
}
const TRANSFORM_PARAMS: TransformParams = { strategy: 'hyde', num_queries: 3 }
const RETRIEVE_PARAMS: RetrieveParams = { mode: 'hybrid', top_k: 10, rrf_k: 60, filters: {} }
const RERANK_PARAMS: RerankParams = { enabled: true, top_n: 5 }
const GENERATE_PARAMS: GenerateParams = {
  max_context_tokens: 4000,
  temperature: 0.2,
  max_answer_tokens: 800,
}
const QUERY_PARAMS = {
  transform: TRANSFORM_PARAMS,
  retrieve: RETRIEVE_PARAMS,
  rerank: RERANK_PARAMS,
  generate: GENERATE_PARAMS,
}

test('createIngestRun posts file_id and collection_id', async () => {
  let body: unknown = null
  server.use(
    http.post('/api/v1/ingest-runs', async ({ request }) => {
      body = await request.json()
      return HttpResponse.json(INGEST_RUN, { status: 201 })
    }),
  )
  const result = await createIngestRun(FILE_ID, COLLECTION.id)
  expect(result).toEqual(INGEST_RUN)
  expect(body).toEqual({ file_id: FILE_ID, collection_id: COLLECTION.id })
})

test('startIngestStage posts the stage params to the chunk stage path', async () => {
  let body: unknown = null
  server.use(
    http.post(`/api/v1/ingest-runs/${RUN_ID}/stages/chunk`, async ({ request }) => {
      body = await request.json()
      return HttpResponse.json(stageRun('chunk'), { status: 202 })
    }),
  )
  const result = await startIngestStage(RUN_ID, 'chunk', INGEST_PARAMS.chunk)
  expect(result).toEqual(stageRun('chunk'))
  expect(body).toEqual({ params: INGEST_PARAMS.chunk })
})

test('runAllIngest posts from_stage null and all params', async () => {
  let body: unknown = null
  server.use(
    http.post(`/api/v1/ingest-runs/${RUN_ID}/run-all`, async ({ request }) => {
      body = await request.json()
      return HttpResponse.json(INGEST_RUN)
    }),
  )
  const result = await runAllIngest(RUN_ID, null, INGEST_PARAMS)
  expect(result).toEqual(INGEST_RUN)
  expect(body).toEqual({ from_stage: null, params: INGEST_PARAMS })
})

test('createQueryRun posts collection_id and question; startQueryStage posts the stage params', async () => {
  let createBody: unknown = null
  let stageBody: unknown = null
  server.use(
    http.post('/api/v1/query-runs', async ({ request }) => {
      createBody = await request.json()
      return HttpResponse.json(QUERY_RUN, { status: 201 })
    }),
    http.post(`/api/v1/query-runs/${QUERY_RUN_ID}/stages/retrieve`, async ({ request }) => {
      stageBody = await request.json()
      return HttpResponse.json(stageRun('retrieve', { run_id: QUERY_RUN_ID }), { status: 202 })
    }),
  )
  const created = await createQueryRun(COLLECTION.id, 'q?')
  expect(created).toEqual(QUERY_RUN)
  expect(createBody).toEqual({ collection_id: COLLECTION.id, question: 'q?' })
  const started = await startQueryStage(QUERY_RUN_ID, 'retrieve', RETRIEVE_PARAMS)
  expect(started).toEqual(stageRun('retrieve', { run_id: QUERY_RUN_ID }))
  expect(stageBody).toEqual({ params: RETRIEVE_PARAMS })
})

test('runAllQuery posts from_stage null and all params', async () => {
  let body: unknown = null
  server.use(
    http.post(`/api/v1/query-runs/${QUERY_RUN_ID}/run-all`, async ({ request }) => {
      body = await request.json()
      return HttpResponse.json(QUERY_RUN, { status: 202 })
    }),
  )
  const result = await runAllQuery(QUERY_RUN_ID, null, QUERY_PARAMS)
  expect(result).toEqual(QUERY_RUN)
  expect(body).toEqual({ from_stage: null, params: QUERY_PARAMS })
})

test('listStageRuns sends run_id and stage as query params', async () => {
  let url: string | null = null
  server.use(
    http.get('/api/v1/stage-runs', ({ request }) => {
      url = request.url
      return HttpResponse.json({ items: [stageRun('parse')] })
    }),
  )
  const result = await listStageRuns(RUN_ID, 'parse')
  expect(result).toEqual({ items: [stageRun('parse')] })
  const query = new URL(url!, window.location.origin).searchParams
  expect(query.get('run_id')).toBe(RUN_ID)
  expect(query.get('stage')).toBe('parse')
})

test('getArtifact returns the artifact JSON; pageImageUrl builds the page image URL', async () => {
  const chunkRun = stageRun('chunk')
  server.use(http.get(`/api/v1/stage-runs/${chunkRun.id}/artifact`, () => HttpResponse.json(CHUNK)))
  const result = await getArtifact<ChunkArtifact>(chunkRun.id)
  expect(result).toEqual(CHUNK)
  expect(pageImageUrl('s', 2)).toBe('/api/v1/stage-runs/s/pages/2')
})

test('startIngestStage rejects with the 409 STAGE_PREREQUISITE_MISSING ApiError', async () => {
  server.use(
    http.post(`/api/v1/ingest-runs/${RUN_ID}/stages/embed`, () =>
      HttpResponse.json(
        {
          error: {
            code: 'STAGE_PREREQUISITE_MISSING',
            message: 'The previous stage has no done version yet',
            details: { stage: 'embed', missing: 'chunk' },
          },
        },
        { status: 409 },
      ),
    ),
  )
  const error = await startIngestStage(RUN_ID, 'embed', INGEST_PARAMS.embed).catch(
    (e: unknown) => e,
  )
  expect(error).toBeInstanceOf(ApiError)
  expect((error as ApiError).code).toBe('STAGE_PREREQUISITE_MISSING')
  expect((error as ApiError).status).toBe(409)
  expect((error as ApiError).details.missing).toBe('chunk')
})
