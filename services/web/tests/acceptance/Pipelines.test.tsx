// F-pipeline-graph (UI)
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'

import { PipelinesPage } from '../../src/pages/PipelinesPage'
import { GRAPH } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'
import { server } from '../setup/server'

test('lists graphs and renders the selected one with its custom node', async () => {
  server.use(http.get('/api/v1/pipeline-graphs', () => HttpResponse.json({ items: [GRAPH] })))
  const user = userEvent.setup()
  renderWithProviders(<PipelinesPage />)
  await user.click(await screen.findByText('chunk / fixed'))
  expect(await screen.findByText('annotator')).toBeInTheDocument()
  expect(screen.getByText('custom')).toBeInTheDocument()
  await user.click(screen.getByText('splitter'))
  expect(screen.getByText('split_by')).toBeInTheDocument()
})

test('empty state', async () => {
  server.use(http.get('/api/v1/pipeline-graphs', () => HttpResponse.json({ items: [] })))
  renderWithProviders(<PipelinesPage />)
  expect(await screen.findByText(/No pipeline graphs reported yet/)).toBeInTheDocument()
})
