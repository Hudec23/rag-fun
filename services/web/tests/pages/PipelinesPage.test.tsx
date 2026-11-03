// PipelinesPage: one "stage / variant" entry per reported graph in the left list (e.g. 'chunk / fixed'),
// the first graph selected by default, clicking another entry renders its graph with <PipelineGraph>,
// empty state prompts to start the worker.
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { vi } from 'vitest'

import type { PipelineGraph } from '../../src/api/types'
import { PipelinesPage } from '../../src/pages/PipelinesPage'
import { GRAPH } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'
import { server } from '../setup/server'

// <PipelineGraph> is @xyflow-based; in page tests replace it with a stub that prints the variant
// of the rendered graph.
vi.mock('../../src/viz/PipelineGraph', () => ({
  PipelineGraph: (props: { graph: { variant: string } }) => (
    <div data-testid="pipeline-graph">variant: {props.graph.variant}</div>
  ),
}))

const EMBED_GRAPH: PipelineGraph = { ...GRAPH, stage: 'embed', variant: 'default' }

test('groups graphs as "chunk / fixed" entries and selects the first by default', async () => {
  server.use(
    http.get('/api/v1/pipeline-graphs', () => HttpResponse.json({ items: [GRAPH, EMBED_GRAPH] })),
  )
  renderWithProviders(<PipelinesPage />)
  await screen.findByText('chunk / fixed')
  expect(screen.getByText('embed / default')).toBeInTheDocument()
  expect(await screen.findByText('variant: fixed')).toBeInTheDocument()
})

test('clicking another entry renders its PipelineGraph', async () => {
  server.use(
    http.get('/api/v1/pipeline-graphs', () => HttpResponse.json({ items: [GRAPH, EMBED_GRAPH] })),
  )
  const user = userEvent.setup()
  renderWithProviders(<PipelinesPage />)
  await screen.findByText('chunk / fixed')
  expect(await screen.findByText('variant: fixed')).toBeInTheDocument()
  await user.click(screen.getByText('embed / default'))
  expect(await screen.findByText('variant: default')).toBeInTheDocument()
})

test('empty: "No pipeline graphs reported yet — is the worker running?"', async () => {
  server.use(http.get('/api/v1/pipeline-graphs', () => HttpResponse.json({ items: [] })))
  renderWithProviders(<PipelinesPage />)
  expect(
    await screen.findByText('No pipeline graphs reported yet — is the worker running?'),
  ).toBeInTheDocument()
})
