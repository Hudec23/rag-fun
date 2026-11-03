// API wrapper tests for src/api/qdrant.ts: each test registers an msw handler that captures the
// request and asserts the exact method, path, query params and body sent.
import { http, HttpResponse } from 'msw'

import { ApiError } from '../../src/api/client'
import { countPoints, getFacet, getPoint, getQdrantInfo, scrollPoints } from '../../src/api/qdrant'
import type {
  FacetResponse,
  PayloadFilter,
  QdrantInfo,
  QdrantPoint,
  ScrollRequest,
  ScrollResponse,
} from '../../src/api/types'
import { COLLECTION, STORE } from '../setup/fixtures'
import { server } from '../setup/server'

const POINT_ID = '00000000000000000000000000000001'
const MISSING_POINT_ID = '5c9e2a5d0b8f4e1a9c7d3b2a1f0e9d8c'
const FILTER: PayloadFilter = { must: [{ key: 'tags', match: { any: ['finance'] } }] }
const SCROLL_REQUEST: ScrollRequest = {
  filter: FILTER,
  limit: 20,
  offset: null,
  with_vectors: false,
}
const SCROLL_RESPONSE: ScrollResponse = {
  points: [{ id: POINT_ID, payload: STORE.payload_sample, vectors: null }],
  next_offset: POINT_ID,
}
const POINT: QdrantPoint = {
  id: POINT_ID,
  payload: STORE.payload_sample,
  vectors: {
    dense: [0.1, 0.2, 0.3],
    sparse: { indices: [10, 42], values: [1.5, 0.75] },
  },
}
const QDRANT_INFO: QdrantInfo = {
  qdrant_name: COLLECTION.qdrant_name,
  exists: true,
  status: 'green',
  points_count: 4,
  dense: { name: 'text-dense', size: 384, distance: 'Cosine' },
  sparse: { name: 'text-sparse', modifier: 'idf' },
  payload_indexes: [
    { key: 'meta.file_id', type: 'keyword', points: 4 },
    { key: 'meta.tags', type: 'keyword', points: 4 },
  ],
}
const FACET_RESPONSE: FacetResponse = {
  key: 'tags',
  values: [
    { value: 'finance', count: 40 },
    { value: 'q3', count: 12 },
  ],
}

test('getQdrantInfo gets the collection qdrant info', async () => {
  server.use(
    http.get(`/api/v1/collections/${COLLECTION.id}/qdrant`, () => HttpResponse.json(QDRANT_INFO)),
  )
  const result = await getQdrantInfo(COLLECTION.id)
  expect(result).toEqual(QDRANT_INFO)
})

test('scrollPoints posts the scroll request as the body', async () => {
  let body: unknown = null
  server.use(
    http.post(`/api/v1/collections/${COLLECTION.id}/qdrant/scroll`, async ({ request }) => {
      body = await request.json()
      return HttpResponse.json(SCROLL_RESPONSE)
    }),
  )
  const result = await scrollPoints(COLLECTION.id, SCROLL_REQUEST)
  expect(result).toEqual(SCROLL_RESPONSE)
  expect(body).toEqual(SCROLL_REQUEST)
})

test('countPoints posts the filter and resolves to the count', async () => {
  let body: unknown = null
  server.use(
    http.post(`/api/v1/collections/${COLLECTION.id}/qdrant/count`, async ({ request }) => {
      body = await request.json()
      return HttpResponse.json({ count: 42 })
    }),
  )
  const result = await countPoints(COLLECTION.id, FILTER)
  expect(result).toBe(42)
  expect(body).toEqual({ filter: FILTER })
})

test('getFacet gets the facet values for a key', async () => {
  server.use(
    http.get(`/api/v1/collections/${COLLECTION.id}/qdrant/facets/tags`, () =>
      HttpResponse.json(FACET_RESPONSE),
    ),
  )
  const result = await getFacet(COLLECTION.id, 'tags')
  expect(result).toEqual(FACET_RESPONSE)
})

test('getPoint gets a point with full vectors; a missing point is a 404 POINT_NOT_FOUND', async () => {
  server.use(
    http.get(`/api/v1/collections/${COLLECTION.id}/qdrant/points/${POINT_ID}`, () =>
      HttpResponse.json(POINT),
    ),
    http.get(`/api/v1/collections/${COLLECTION.id}/qdrant/points/${MISSING_POINT_ID}`, () =>
      HttpResponse.json(
        {
          error: {
            code: 'POINT_NOT_FOUND',
            message: 'Qdrant point not found',
            details: { point_id: MISSING_POINT_ID },
          },
        },
        { status: 404 },
      ),
    ),
  )
  const point = await getPoint(COLLECTION.id, POINT_ID)
  expect(point).toEqual(POINT)
  expect(point.vectors?.dense).toEqual([0.1, 0.2, 0.3])
  const error = await getPoint(COLLECTION.id, MISSING_POINT_ID).catch((e: unknown) => e)
  expect(error).toBeInstanceOf(ApiError)
  expect((error as ApiError).code).toBe('POINT_NOT_FOUND')
  expect((error as ApiError).status).toBe(404)
  expect((error as ApiError).details.point_id).toBe(MISSING_POINT_ID)
})
