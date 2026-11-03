// F-chunk (UI) — LengthHistogram
import { screen } from '@testing-library/react'

import { LengthHistogram } from '../../src/viz/LengthHistogram'
import { renderWithProviders } from '../setup/render'

function renderHistogram(binEdges: number[], counts: number[]) {
  return renderWithProviders(<LengthHistogram binEdges={binEdges} counts={counts} />)
}

function figure() {
  return JSON.parse(screen.getByTestId('plot').getAttribute('data-figure')!)
}

function titleText(fig: unknown): string {
  const title = (fig as { layout?: { title?: string | { text?: string } } }).layout?.title
  return typeof title === 'string' ? title : (title?.text ?? '')
}

test('renders a bar trace of bin centers with counts and a "Chunk length" title', () => {
  renderHistogram([0, 10, 20], [2, 3])
  const fig = figure()
  expect(fig.data[0].x).toEqual([5, 15])
  expect(fig.data[0].y).toEqual([2, 3])
  expect(fig.data[0].type).toBe('bar')
  expect(titleText(fig)).toContain('Chunk length')
})

test('shows "No chunks" and no plot when counts are empty', () => {
  renderHistogram([0, 10, 20], [])
  expect(screen.getByText('No chunks')).toBeInTheDocument()
  expect(screen.queryByTestId('plot')).toBeNull()
})

test('passes the bin widths as the width of the bar trace', () => {
  renderHistogram([0, 10, 20], [2, 3])
  expect(figure().data[0].width).toEqual([10, 10])
})
