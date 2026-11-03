// FilterBuilder (F-qdrant-browser): one row per must condition; key select (aria-label "key");
// keyword keys → "is any of" multi-select (aria-label "values") fed by getFacet with options
// "value (count)"; page/chunk_index → "between" number inputs (aria-labels "from"/"to").
// "Add condition" appends {key: 'tags', match: {any: []}}; only complete conditions are emitted.
import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { vi } from 'vitest'

import { FilterBuilder } from '../../src/components/FilterBuilder'
import { renderWithProviders } from '../setup/render'
import { server } from '../setup/server'

test('clicking Add condition appends a tags row and emits nothing yet', async () => {
  const onChange = vi.fn()
  const user = userEvent.setup()
  server.use(
    http.get('/api/v1/collections/c/qdrant/facets/tags', () =>
      HttpResponse.json({ key: 'tags', values: [] }),
    ),
  )
  renderWithProviders(<FilterBuilder collectionId="c" value={{ must: [] }} onChange={onChange} />)
  await user.click(screen.getByRole('button', { name: 'Add condition' }))
  const key = screen.getByRole('combobox', { name: 'key' })
  expect(key).toHaveValue('tags')
  expect(within(key).getByRole('option', { name: 'page' })).toBeInTheDocument()
  expect(screen.getByText('is any of')).toBeInTheDocument()
  expect(screen.getByRole('listbox', { name: 'values' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'remove condition' })).toBeInTheDocument()
  expect(onChange).not.toHaveBeenCalled()
})

test('keyword row lists facet options as "value (count)" and selecting one emits any', async () => {
  const onChange = vi.fn()
  const user = userEvent.setup()
  server.use(
    http.get('/api/v1/collections/c/qdrant/facets/tags', () =>
      HttpResponse.json({ key: 'tags', values: [{ value: 'finance', count: 4 }] }),
    ),
  )
  renderWithProviders(<FilterBuilder collectionId="c" value={{ must: [] }} onChange={onChange} />)
  await user.click(screen.getByRole('button', { name: 'Add condition' }))
  const values = screen.getByRole('listbox', { name: 'values' })
  await within(values).findByRole('option', { name: 'finance (4)' })
  expect(onChange).not.toHaveBeenCalled()
  await user.selectOptions(values, 'finance')
  expect(onChange).toHaveBeenCalledTimes(1)
  expect(onChange).toHaveBeenCalledWith({ must: [{ key: 'tags', match: { any: ['finance'] } }] })
})

test('page key shows between inputs and typing from emits range gte', async () => {
  const onChange = vi.fn()
  const user = userEvent.setup()
  server.use(
    http.get('/api/v1/collections/c/qdrant/facets/tags', () =>
      HttpResponse.json({ key: 'tags', values: [] }),
    ),
  )
  renderWithProviders(<FilterBuilder collectionId="c" value={{ must: [] }} onChange={onChange} />)
  await user.click(screen.getByRole('button', { name: 'Add condition' }))
  await user.selectOptions(screen.getByRole('combobox', { name: 'key' }), 'page')
  expect(screen.getByText('between')).toBeInTheDocument()
  expect(screen.queryByText('is any of')).not.toBeInTheDocument()
  const from = screen.getByLabelText('from')
  const to = screen.getByLabelText('to')
  expect(from).toHaveAttribute('type', 'number')
  expect(to).toHaveAttribute('type', 'number')
  // jest-dom 7 reads number inputs as numbers: empty -> null
  expect(from).toHaveValue(null)
  expect(to).toHaveValue(null)
  await user.type(from, '1')
  expect(onChange).toHaveBeenLastCalledWith({ must: [{ key: 'page', range: { gte: 1 } }] })
})

test('clicking remove condition removes the row and emits an empty must', async () => {
  const onChange = vi.fn()
  const user = userEvent.setup()
  server.use(
    http.get('/api/v1/collections/c/qdrant/facets/tags', () =>
      HttpResponse.json({ key: 'tags', values: [{ value: 'finance', count: 4 }] }),
    ),
  )
  renderWithProviders(
    <FilterBuilder
      collectionId="c"
      value={{ must: [{ key: 'tags', match: { any: ['finance'] } }] }}
      onChange={onChange}
    />,
  )
  expect(screen.getByRole('combobox', { name: 'key' })).toHaveValue('tags')
  const values = screen.getByRole('listbox', { name: 'values' })
  await within(values).findByRole('option', { name: 'finance (4)' })
  expect(values).toHaveValue(['finance'])
  await user.click(screen.getByRole('button', { name: 'remove condition' }))
  expect(onChange).toHaveBeenCalledTimes(1)
  expect(onChange).toHaveBeenCalledWith({ must: [] })
  expect(screen.queryByRole('combobox', { name: 'key' })).not.toBeInTheDocument()
  expect(screen.queryByRole('listbox', { name: 'values' })).not.toBeInTheDocument()
})

test('value with existing conditions renders pre-filled', async () => {
  const onChange = vi.fn()
  server.use(
    http.get('/api/v1/collections/c/qdrant/facets/tags', () =>
      HttpResponse.json({ key: 'tags', values: [{ value: 'finance', count: 4 }] }),
    ),
  )
  renderWithProviders(
    <FilterBuilder
      collectionId="c"
      value={{
        must: [
          { key: 'tags', match: { any: ['finance'] } },
          { key: 'page', range: { gte: 1, lte: 3 } },
        ],
      }}
      onChange={onChange}
    />,
  )
  const keySelects = screen.getAllByRole('combobox', { name: 'key' })
  expect(keySelects[0]).toHaveValue('tags')
  expect(keySelects[1]).toHaveValue('page')
  const values = screen.getByRole('listbox', { name: 'values' })
  await within(values).findByRole('option', { name: 'finance (4)' })
  expect(values).toHaveValue(['finance'])
  expect(screen.getByLabelText('from')).toHaveValue(1)
  expect(screen.getByLabelText('to')).toHaveValue(3)
  expect(onChange).not.toHaveBeenCalled()
})
