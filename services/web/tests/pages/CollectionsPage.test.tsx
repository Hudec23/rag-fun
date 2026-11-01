// Example test file (house style for web tests): msw handlers per test, renderWithProviders,
// queries by role/text, findBy* for async data.
import { screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { vi } from 'vitest'

import { CollectionsPage } from '../../src/pages/CollectionsPage'
import { COLLECTION } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'
import { server } from '../setup/server'

vi.mock('../../src/components/CreateCollectionForm', () => ({ CreateCollectionForm: () => null }))

test('lists collections with their models', async () => {
  server.use(http.get('/api/v1/collections', () => HttpResponse.json({ items: [COLLECTION] })))
  renderWithProviders(<CollectionsPage />)
  expect(await screen.findByText('default')).toBeInTheDocument()
  expect(screen.getByText('bge-m3 · 1024d · Qdrant/bm25')).toBeInTheDocument()
})

test('shows the api error code and message', async () => {
  server.use(
    http.get('/api/v1/collections', () =>
      HttpResponse.json(
        {
          error: {
            code: 'DEPENDENCY_UNAVAILABLE',
            message: 'A backing service is unavailable',
            details: {},
          },
        },
        { status: 503 },
      ),
    ),
  )
  renderWithProviders(<CollectionsPage />)
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'DEPENDENCY_UNAVAILABLE: A backing service is unavailable',
  )
})
