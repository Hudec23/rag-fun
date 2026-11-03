// PipelineGraph (F-pipeline-graph): read-only @xyflow/react view — one node per graph node
// (label = name, sublabel = class name after the last '.', "custom" badge for custom classes),
// one edge per graph edge (label "sender_socket → receiver_socket"); clicking a node shows its
// init_params as a name/value table beside the graph.
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { PipelineGraph } from '../../src/viz/PipelineGraph'
import { GRAPH } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

test('shows node labels with class names as sublabels', () => {
  renderWithProviders(<PipelineGraph graph={GRAPH} />)
  expect(screen.getByText('splitter')).toBeInTheDocument()
  expect(screen.getByText('annotator')).toBeInTheDocument()
  expect(screen.getByText('DocumentSplitter')).toBeInTheDocument()
  expect(screen.getByText('ChunkAnnotator')).toBeInTheDocument()
})

test('marks custom nodes with a custom badge', () => {
  renderWithProviders(<PipelineGraph graph={GRAPH} />)
  expect(screen.getByText('custom')).toBeInTheDocument()
})

test('shows edge labels as sender socket → receiver socket', () => {
  renderWithProviders(<PipelineGraph graph={GRAPH} />)
  expect(screen.getByText('documents → documents')).toBeInTheDocument()
})

test('shows the clicked node init params as a name/value table', async () => {
  const user = userEvent.setup()
  renderWithProviders(<PipelineGraph graph={GRAPH} />)
  await user.click(screen.getByText('splitter'))
  expect(screen.getByRole('table')).toBeInTheDocument()
  expect(screen.getByText('split_by')).toBeInTheDocument()
  expect(screen.getByText('"word"')).toBeInTheDocument()
})
