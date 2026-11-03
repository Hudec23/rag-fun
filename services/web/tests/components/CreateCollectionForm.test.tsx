// CreateCollectionForm (F-collections): name input ("Name"), dense and sparse model selects,
// "Create" button; submit → POST /collections; success → cleared name + onCreated();
// ApiError → ErrorBox alert.
import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { vi } from 'vitest'

import { CreateCollectionForm } from '../../src/components/CreateCollectionForm'
import { COLLECTION } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'
import { server } from '../setup/server'

test('"Create" disabled while Name is empty', () => {
  renderWithProviders(<CreateCollectionForm />)
  expect(screen.getByLabelText('Name')).toHaveValue('')
  expect(screen.getByRole('button', { name: 'Create' })).toBeDisabled()
})

test("filling name 'exp' and choosing dense 'all-minilm' posts the default sparse model, clears the name and calls onCreated", async () => {
  let body: unknown = undefined
  server.use(
    http.post('/api/v1/collections', async ({ request }) => {
      body = await request.json()
      return HttpResponse.json({ ...COLLECTION, name: 'exp' }, { status: 201 })
    }),
  )
  const onCreated = vi.fn()
  const user = userEvent.setup()
  renderWithProviders(<CreateCollectionForm onCreated={onCreated} />)
  await user.type(screen.getByLabelText('Name'), 'exp')
  await user.selectOptions(screen.getByLabelText('Dense model'), 'all-minilm')
  await user.click(screen.getByRole('button', { name: 'Create' }))
  await waitFor(() =>
    expect(body).toEqual({
      name: 'exp',
      dense_model: 'all-minilm',
      sparse_model: 'Qdrant/bm25',
    }),
  )
  await waitFor(() => expect(onCreated).toHaveBeenCalledTimes(1))
  await waitFor(() => expect(screen.getByLabelText('Name')).toHaveValue(''))
})

test('a 409 response shows the COLLECTION_NAME_TAKEN alert', async () => {
  server.use(
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
  const onCreated = vi.fn()
  const user = userEvent.setup()
  renderWithProviders(<CreateCollectionForm onCreated={onCreated} />)
  await user.type(screen.getByLabelText('Name'), 'exp')
  await user.click(screen.getByRole('button', { name: 'Create' }))
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'COLLECTION_NAME_TAKEN: A collection with this name already exists',
  )
  expect(onCreated).not.toHaveBeenCalled()
})

test('the Dense model select has exactly the 4 dense models and the Sparse model select the 2 sparse models', () => {
  renderWithProviders(<CreateCollectionForm />)
  const dense = screen.getByLabelText('Dense model')
  const sparse = screen.getByLabelText('Sparse model')
  expect(dense).toHaveValue('bge-m3')
  expect(sparse).toHaveValue('Qdrant/bm25')
  expect(
    (within(dense).getAllByRole('option') as HTMLOptionElement[])
      .map((option) => option.value)
      .sort(),
  ).toEqual(['all-minilm', 'bge-m3', 'mxbai-embed-large', 'nomic-embed-text'])
  expect(
    (within(sparse).getAllByRole('option') as HTMLOptionElement[])
      .map((option) => option.value)
      .sort(),
  ).toEqual(['Qdrant/bm25', 'prithivida/Splade_PP_en_v1'])
})
