// F-collections (UI)
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'

import type { Collection } from '../../src/api/types'
import { CollectionsPage } from '../../src/pages/CollectionsPage'
import { COLLECTION } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'
import { server } from '../setup/server'

test('creates a collection and refreshes the list', async () => {
  let items = [COLLECTION]
  let body: unknown = null
  server.use(
    http.get('/api/v1/collections', () => HttpResponse.json({ items })),
    http.post('/api/v1/collections', async ({ request }) => {
      body = await request.json()
      const created: Collection = {
        ...COLLECTION,
        id: '019a4b2c-1d00-7b00-8000-0000000000bb',
        name: 'experiments',
        dense_model: 'all-minilm',
        dense_dims: 384,
      }
      items = [COLLECTION, created]
      return HttpResponse.json(created, { status: 201 })
    }),
  )
  const user = userEvent.setup()
  renderWithProviders(<CollectionsPage />)
  await screen.findByText('default')
  expect(screen.getByRole('button', { name: 'Create' })).toBeDisabled()
  await user.type(screen.getByLabelText('Name'), 'experiments')
  await user.selectOptions(screen.getByLabelText('Dense model'), 'all-minilm')
  await user.click(screen.getByRole('button', { name: 'Create' }))
  await waitFor(() =>
    expect(body).toEqual({
      name: 'experiments',
      dense_model: 'all-minilm',
      sparse_model: 'Qdrant/bm25',
    }),
  )
  expect(await screen.findByText('experiments')).toBeInTheDocument()
})

test('shows COLLECTION_NAME_TAKEN', async () => {
  server.use(
    http.get('/api/v1/collections', () => HttpResponse.json({ items: [COLLECTION] })),
    http.post('/api/v1/collections', () =>
      HttpResponse.json(
        {
          error: {
            code: 'COLLECTION_NAME_TAKEN',
            message: 'A collection with this name already exists',
            details: {},
          },
        },
        { status: 409 },
      ),
    ),
  )
  const user = userEvent.setup()
  renderWithProviders(<CollectionsPage />)
  await screen.findByText('default')
  await user.type(screen.getByLabelText('Name'), 'default')
  await user.click(screen.getByRole('button', { name: 'Create' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('COLLECTION_NAME_TAKEN')
})
