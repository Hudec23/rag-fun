// QdrantBrowserPage: info card (status, points, payload indexes), points table, "Load more" with
// next_offset, row click → side panel (first 16 dense dims + "… (n more)"), collection select
// navigates to /qdrant/<id>.
import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes, useParams } from 'react-router'
import { vi } from 'vitest'

import type { Collection } from '../../src/api/types'
import { QdrantBrowserPage } from '../../src/pages/QdrantBrowserPage'
import { COLLECTION, STORE } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'
import { server } from '../setup/server'

vi.mock('../../src/components/FilterBuilder', () => ({ FilterBuilder: () => null }))

const POINT_ID = '0123456789abcdef0123456789abcdef'
const POINT = { id: POINT_ID, payload: STORE.payload_sample, vectors: null }
const POINT_WITH_VECTORS = {
  ...POINT,
  vectors: { dense: Array(384).fill(0.1), sparse: { indices: [1], values: [1] } },
}
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
const NEXT_OFFSET = 'ffffffffffffffffffffffffffffffff'
const COLLECTION_2: Collection = {
  ...COLLECTION,
  id: '019a4b2c-1d00-7b00-8000-0000000000bb',
  name: 'second',
  qdrant_name: 'rf_019a4b2c1d007b0080000000000000bb',
}

/** The endpoints the page hits on load without filters: collections (for the select),
 *  qdrant info, scroll (one point, no next page) and count. */
function qdrantHandlers() {
  return [
    http.get('/api/v1/collections', () => HttpResponse.json({ items: [COLLECTION] })),
    http.get(`/api/v1/collections/${COLLECTION.id}/qdrant`, () => HttpResponse.json(INFO)),
    http.post(`/api/v1/collections/${COLLECTION.id}/qdrant/scroll`, () =>
      HttpResponse.json({ points: [POINT], next_offset: null }),
    ),
    http.post(`/api/v1/collections/${COLLECTION.id}/qdrant/count`, () =>
      HttpResponse.json({ count: 1 }),
    ),
  ]
}

/** Route params of the mounted page, for the navigation assertion (last test). */
function QdrantRouteMarker() {
  const { collectionId } = useParams()
  return <div data-testid="qdrant-route">{collectionId ?? ''}</div>
}

test('shows the info card: status, points count and payload index rows', async () => {
  server.use(...qdrantHandlers())
  renderWithProviders(<QdrantBrowserPage />, {
    path: `/qdrant/${COLLECTION.id}`,
    route: '/qdrant/:collectionId?',
  })
  expect(await screen.findByText('green')).toBeInTheDocument()
  expect(await screen.findByText('4 points')).toBeInTheDocument()
  expect(await screen.findByText('text-dense')).toBeInTheDocument()
  expect(await screen.findByText('text-sparse')).toBeInTheDocument()
  expect(await screen.findByText('meta.file_id')).toBeInTheDocument()
  expect(await screen.findByText('meta.tags')).toBeInTheDocument()
})

test('shows the first points row: id, filename, page and element_type', async () => {
  server.use(...qdrantHandlers())
  renderWithProviders(<QdrantBrowserPage />, {
    path: `/qdrant/${COLLECTION.id}`,
    route: '/qdrant/:collectionId?',
  })
  const row = (await screen.findByText('q3-report.pdf')).closest('tr')!
  expect(within(row).getByText('01234567')).toBeInTheDocument()
  expect(within(row).getByText('1')).toBeInTheDocument()
  expect(within(row).getByText('text')).toBeInTheDocument()
})

test('shows "Load more" when next_offset is set and sends it as offset', async () => {
  const scrolls: unknown[] = []
  server.use(
    http.get('/api/v1/collections', () => HttpResponse.json({ items: [COLLECTION] })),
    http.get(`/api/v1/collections/${COLLECTION.id}/qdrant`, () => HttpResponse.json(INFO)),
    http.post(`/api/v1/collections/${COLLECTION.id}/qdrant/scroll`, async ({ request }) => {
      const body = await request.json()
      scrolls.push(body)
      return HttpResponse.json({ points: [POINT], next_offset: NEXT_OFFSET })
    }),
    http.post(`/api/v1/collections/${COLLECTION.id}/qdrant/count`, () =>
      HttpResponse.json({ count: 1 }),
    ),
  )
  const user = userEvent.setup()
  renderWithProviders(<QdrantBrowserPage />, {
    path: `/qdrant/${COLLECTION.id}`,
    route: '/qdrant/:collectionId?',
  })
  await screen.findByText('q3-report.pdf')
  expect(scrolls).toEqual([{ filter: { must: [] }, limit: 20, offset: null, with_vectors: false }])
  const button = await screen.findByRole('button', { name: 'Load more' })
  await user.click(button)
  await waitFor(() =>
    expect(scrolls).toContainEqual({
      filter: { must: [] },
      limit: 20,
      offset: NEXT_OFFSET,
      with_vectors: false,
    }),
  )
})

test('row click opens the side panel with the first 16 dims and "… (368 more)"', async () => {
  server.use(
    ...qdrantHandlers(),
    http.get(`/api/v1/collections/${COLLECTION.id}/qdrant/points/${POINT_ID}`, () =>
      HttpResponse.json(POINT_WITH_VECTORS),
    ),
  )
  const user = userEvent.setup()
  renderWithProviders(<QdrantBrowserPage />, {
    path: `/qdrant/${COLLECTION.id}`,
    route: '/qdrant/:collectionId?',
  })
  await user.click(await screen.findByText('q3-report.pdf'))
  expect(await screen.findByText(/… \(368 more\)/)).toBeInTheDocument()
  const pre = document.querySelector('pre')!
  expect((pre.textContent ?? '').match(/0\.1/g)?.length).toBe(16)
})

test('collection select change navigates to /qdrant/<id>', async () => {
  let fetchedSecond = false
  server.use(
    http.get('/api/v1/collections', () => HttpResponse.json({ items: [COLLECTION, COLLECTION_2] })),
    http.get('/api/v1/collections/:collectionId/qdrant', ({ params }) => {
      if (params.collectionId === COLLECTION_2.id) fetchedSecond = true
      return HttpResponse.json(INFO)
    }),
    http.post('/api/v1/collections/:collectionId/qdrant/scroll', () =>
      HttpResponse.json({ points: [POINT], next_offset: null }),
    ),
    http.post('/api/v1/collections/:collectionId/qdrant/count', () =>
      HttpResponse.json({ count: 1 }),
    ),
  )
  const user = userEvent.setup()
  renderWithProviders(
    <Routes>
      <Route
        path="/qdrant/:collectionId?"
        element={
          <>
            <QdrantRouteMarker />
            <QdrantBrowserPage />
          </>
        }
      />
    </Routes>,
    { path: `/qdrant/${COLLECTION.id}` },
  )
  await screen.findByText('q3-report.pdf')
  await user.selectOptions(
    await screen.findByRole('combobox', { name: 'Collection' }),
    COLLECTION_2.id,
  )
  const marker = screen.getByTestId('qdrant-route')
  await waitFor(() => expect(marker).toHaveTextContent(COLLECTION_2.id))
  await waitFor(() => expect(fetchedSecond).toBe(true))
})
