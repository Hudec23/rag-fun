// F-qdrant-browser (UI)
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'

import { QdrantBrowserPage } from '../../src/pages/QdrantBrowserPage'
import { COLLECTION, STORE } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'
import { server } from '../setup/server'

const INFO = {
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
const POINT = { id: 'a'.repeat(32), payload: STORE.payload_sample, vectors: null }

test('shows info, points and filters by tag', async () => {
  const scrolls: unknown[] = []
  server.use(
    http.get('/api/v1/collections', () => HttpResponse.json({ items: [COLLECTION] })),
    http.get(`/api/v1/collections/${COLLECTION.id}/qdrant`, () => HttpResponse.json(INFO)),
    http.post(`/api/v1/collections/${COLLECTION.id}/qdrant/scroll`, async ({ request }) => {
      scrolls.push(await request.json())
      return HttpResponse.json({ points: [POINT], next_offset: null })
    }),
    http.post(`/api/v1/collections/${COLLECTION.id}/qdrant/count`, () =>
      HttpResponse.json({ count: 1 }),
    ),
    http.get(`/api/v1/collections/${COLLECTION.id}/qdrant/facets/:key`, () =>
      HttpResponse.json({ key: 'tags', values: [{ value: 'finance', count: 4 }] }),
    ),
    http.get(`/api/v1/collections/${COLLECTION.id}/qdrant/points/:id`, () =>
      HttpResponse.json({
        ...POINT,
        vectors: { dense: Array(384).fill(0.1), sparse: { indices: [1], values: [1] } },
      }),
    ),
  )
  const user = userEvent.setup()
  renderWithProviders(<QdrantBrowserPage />, {
    path: `/qdrant/${COLLECTION.id}`,
    route: '/qdrant/:collectionId?',
  })
  expect(await screen.findByText('text-dense')).toBeInTheDocument()
  expect(await screen.findByText('q3-report.pdf')).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Add condition' }))
  await user.selectOptions(await screen.findByRole('listbox'), 'finance')
  await waitFor(() =>
    expect(scrolls).toContainEqual({
      filter: { must: [{ key: 'tags', match: { any: ['finance'] } }] },
      limit: 20,
      offset: null,
      with_vectors: false,
    }),
  )
  await user.click(screen.getByText('q3-report.pdf'))
  expect(await screen.findByText(/… \(368 more\)/)).toBeInTheDocument()
})

test('empty collection hint', async () => {
  server.use(
    http.get('/api/v1/collections', () => HttpResponse.json({ items: [COLLECTION] })),
    http.get(`/api/v1/collections/${COLLECTION.id}/qdrant`, () =>
      HttpResponse.json({
        ...INFO,
        exists: false,
        status: null,
        points_count: null,
        dense: null,
        sparse: null,
        payload_indexes: [],
      }),
    ),
    http.post(`/api/v1/collections/${COLLECTION.id}/qdrant/scroll`, () =>
      HttpResponse.json({ points: [], next_offset: null }),
    ),
    http.post(`/api/v1/collections/${COLLECTION.id}/qdrant/count`, () =>
      HttpResponse.json({ count: 0 }),
    ),
  )
  renderWithProviders(<QdrantBrowserPage />, {
    path: `/qdrant/${COLLECTION.id}`,
    route: '/qdrant/:collectionId?',
  })
  expect(await screen.findByText(/Nothing stored yet in this collection/)).toBeInTheDocument()
})
