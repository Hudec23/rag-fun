// API wrapper tests for src/api/batches.ts + files.ts: each test registers an msw handler that
// captures the request and asserts the exact method, path, query params and body sent.
import { http, HttpResponse } from 'msw'

import { ingestBatch, listBatches, updateBatch, uploadBatch } from '../../src/api/batches'
import { ApiError } from '../../src/api/client'
import { deleteFile, listFiles, updateFileTags } from '../../src/api/files'
import type {
  Batch,
  BatchList,
  BatchWithFiles,
  FileItem,
  FileList,
  IngestParamsAll,
  IngestRun,
} from '../../src/api/types'
import { COLLECTION, FILE_ID, RUN_ID } from '../setup/fixtures'
import { server } from '../setup/server'

const BATCH_ID = '019a4b2c-1e00-7b00-8000-000000000001'
const CREATED_AT = '2026-11-01T18:22:05.123Z'

const BATCH: Batch = {
  id: BATCH_ID,
  name: 'Q3 reports',
  tags: ['finance'],
  file_count: 2,
  created_at: CREATED_AT,
}
const FILE_A: FileItem = {
  id: FILE_ID,
  batch_id: BATCH_ID,
  filename: 'q3-report.pdf',
  mime: 'application/pdf',
  size_bytes: 482113,
  sha256: 'a'.repeat(64),
  tags: [],
  created_at: CREATED_AT,
}
const FILE_B: FileItem = {
  id: '019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a02',
  batch_id: BATCH_ID,
  filename: 'notes.md',
  mime: 'text/markdown',
  size_bytes: 12,
  sha256: 'b'.repeat(64),
  tags: [],
  created_at: CREATED_AT,
}
const BATCH_WITH_FILES: BatchWithFiles = {
  batch: BATCH,
  files: [FILE_A, FILE_B],
}
const BATCH_LIST: BatchList = {
  items: [BATCH],
  page: { total: 1, limit: 10, offset: 20 },
}
const FILE_LIST: FileList = {
  items: [FILE_A],
  page: { total: 1, limit: 50, offset: 0 },
}
const INGEST_RUN: IngestRun = {
  id: RUN_ID,
  file: FILE_A,
  collection_id: COLLECTION.id,
  created_at: CREATED_AT,
  run_all_pending: ['parse', 'chunk', 'embed', 'store'],
  stages: { parse: null, chunk: null, embed: null, store: null },
}
const INGEST_DEFAULTS: IngestParamsAll = {
  parse: { strategy: 'docling_layout', extract_tables: true, page_images: true },
  chunk: { strategy: 'fixed', split_by: 'word', length: 200, overlap: 20 },
  embed: { batch_size: 16 },
  store: {},
}

const fileA = new File(['%PDF'], 'q3-report.pdf', { type: 'application/pdf' })
const fileB = new File(['# h'], 'notes.md', { type: 'text/markdown' })

test('uploadBatch posts a multipart form with files, name and tags', async () => {
  let form: FormData | null = null
  let contentType: string | null = null
  server.use(
    http.post('/api/v1/batches', async ({ request }) => {
      form = await request.formData()
      contentType = request.headers.get('content-type')
      return HttpResponse.json(BATCH_WITH_FILES, { status: 201 })
    }),
  )
  const result = await uploadBatch([fileA, fileB], 'n', ['x', 'y'])
  expect(result).toEqual(BATCH_WITH_FILES)
  expect(contentType).not.toBeNull()
  expect(contentType!.startsWith('multipart/form-data')).toBe(true)
  expect(form).not.toBeNull()
  const files = form!.getAll('files') as File[]
  expect(files).toHaveLength(2)
  expect(files.map((file) => file.name)).toEqual(['q3-report.pdf', 'notes.md'])
  expect(form!.get('name')).toBe('n')
  expect(form!.get('tags')).toBe('x,y')
})

test('uploadBatch omits name and tags when name is null and tags are empty', async () => {
  let form: FormData | null = null
  server.use(
    http.post('/api/v1/batches', async ({ request }) => {
      form = await request.formData()
      return HttpResponse.json(BATCH_WITH_FILES, { status: 201 })
    }),
  )
  const result = await uploadBatch([fileB], null, [])
  expect(result).toEqual(BATCH_WITH_FILES)
  expect(form).not.toBeNull()
  expect(form!.getAll('files')).toHaveLength(1)
  expect(form!.has('name')).toBe(false)
  expect(form!.has('tags')).toBe(false)
})

test('listBatches sends limit and offset as query params', async () => {
  let url: string | null = null
  server.use(
    http.get('/api/v1/batches', ({ request }) => {
      url = request.url
      return HttpResponse.json(BATCH_LIST)
    }),
  )
  const result = await listBatches(10, 20)
  expect(result).toEqual(BATCH_LIST)
  const query = new URL(url!, window.location.origin).searchParams
  expect(query.get('limit')).toBe('10')
  expect(query.get('offset')).toBe('20')
})

test('updateBatch sends only the given patch fields', async () => {
  let body: unknown = null
  server.use(
    http.patch(`/api/v1/batches/${BATCH_ID}`, async ({ request }) => {
      body = await request.json()
      return HttpResponse.json(BATCH)
    }),
  )
  const result = await updateBatch(BATCH_ID, { tags: ['a'] })
  expect(result).toEqual(BATCH)
  expect(body).toEqual({ tags: ['a'] })
})

test('ingestBatch posts collection_id and params', async () => {
  let body: unknown = null
  server.use(
    http.post(`/api/v1/batches/${BATCH_ID}/ingest`, async ({ request }) => {
      body = await request.json()
      return HttpResponse.json({ items: [INGEST_RUN] }, { status: 202 })
    }),
  )
  const result = await ingestBatch(BATCH_ID, COLLECTION.id, INGEST_DEFAULTS)
  expect(result).toEqual({ items: [INGEST_RUN] })
  expect(body).toEqual({ collection_id: COLLECTION.id, params: INGEST_DEFAULTS })
})

test('listFiles sends only the provided filters', async () => {
  let url: string | null = null
  server.use(
    http.get('/api/v1/files', ({ request }) => {
      url = request.url
      return HttpResponse.json(FILE_LIST)
    }),
  )
  const result = await listFiles({ batch_id: 'b', tag: undefined })
  expect(result).toEqual(FILE_LIST)
  const query = new URL(url!, window.location.origin).searchParams
  expect(query.get('batch_id')).toBe('b')
  expect(query.has('tag')).toBe(false)
  expect(query.has('limit')).toBe(false)
  expect(query.has('offset')).toBe(false)
  expect(query.has('mime')).toBe(false)
})

test('updateFileTags patches the tags; deleteFile resolves undefined on 204', async () => {
  let body: unknown = null
  server.use(
    http.patch(`/api/v1/files/${FILE_ID}`, async ({ request }) => {
      body = await request.json()
      return HttpResponse.json({ ...FILE_A, tags: ['t'] })
    }),
    http.delete(`/api/v1/files/${FILE_ID}`, () => new HttpResponse(null, { status: 204 })),
  )
  const updated = await updateFileTags(FILE_ID, ['t'])
  expect(updated).toEqual({ ...FILE_A, tags: ['t'] })
  expect(body).toEqual({ tags: ['t'] })
  expect(await deleteFile(FILE_ID)).toBeUndefined()
})

test('uploadBatch rejects with the ApiError code and status from a 415 body', async () => {
  server.use(
    http.post('/api/v1/batches', () =>
      HttpResponse.json(
        {
          error: {
            code: 'UNSUPPORTED_FILE_TYPE',
            message: 'File type is not supported',
            details: { filename: 'notes.rtf' },
          },
        },
        { status: 415 },
      ),
    ),
  )
  const error = await uploadBatch([new File(['rtf'], 'notes.rtf')], 'n', []).catch(
    (e: unknown) => e,
  )
  expect(error).toBeInstanceOf(ApiError)
  expect(error as ApiError).toMatchObject({
    code: 'UNSUPPORTED_FILE_TYPE',
    status: 415,
    message: 'File type is not supported',
    details: { filename: 'notes.rtf' },
  })
})
