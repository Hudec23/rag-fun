// F-embed (UI) — VectorHeatmap
import { screen } from '@testing-library/react'

import { VectorHeatmap } from '../../src/viz/VectorHeatmap'
import { renderWithProviders } from '../setup/render'

const VECTORS = [
  [0.25, -0.5, 0.125],
  [-0.75, 0.375, -0.25],
]
const LABELS = ['chunk 1', 'chunk 2']

function renderHeatmap(overrides: Partial<Parameters<typeof VectorHeatmap>[0]> = {}) {
  return renderWithProviders(<VectorHeatmap vectors={VECTORS} labels={LABELS} {...overrides} />)
}

function figure() {
  return JSON.parse(screen.getByTestId('plot').getAttribute('data-figure')!)
}

function titleText(fig: unknown): string {
  const title = (fig as { layout?: { title?: string | { text?: string } } }).layout?.title
  return typeof title === 'string' ? title : (title?.text ?? '')
}

test('renders a heatmap trace with z = vectors, y = labels, colorscale RdBu and zmid 0', () => {
  renderHeatmap()
  const trace = figure().data[0]
  expect(trace.type).toBe('heatmap')
  expect(trace.z).toEqual(VECTORS)
  expect(trace.y).toEqual(LABELS)
  expect(trace.colorscale).toBe('RdBu')
  expect(trace.zmid).toBe(0)
})

test('shows the "Dense vectors (2 × 3)" title', () => {
  renderHeatmap()
  expect(titleText(figure())).toContain('2 × 3')
})

test('shows "No vectors" when vectors are empty', () => {
  renderHeatmap({ vectors: [], labels: [] })
  expect(screen.getByText('No vectors')).toBeInTheDocument()
  expect(screen.queryByTestId('plot')).toBeNull()
})
