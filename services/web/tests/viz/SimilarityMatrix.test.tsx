// F-embed (UI) — SimilarityMatrix
import { screen } from '@testing-library/react'

import { SimilarityMatrix } from '../../src/viz/SimilarityMatrix'
import { EMBED } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

const MATRIX = EMBED.similarity
const LABELS = ['#0', '#1', '#2', '#3']

function renderMatrix(overrides: Partial<Parameters<typeof SimilarityMatrix>[0]> = {}) {
  return renderWithProviders(<SimilarityMatrix matrix={MATRIX} labels={LABELS} {...overrides} />)
}

function figure() {
  return JSON.parse(screen.getByTestId('plot').getAttribute('data-figure')!)
}

function titleText(fig: unknown): string {
  const title = (fig as { layout?: { title?: string | { text?: string } } }).layout?.title
  return typeof title === 'string' ? title : (title?.text ?? '')
}

test('renders a heatmap trace with z = matrix, x = y = labels, Viridis colorscale, zmin -1 and zmax 1', () => {
  renderMatrix()
  const trace = figure().data[0]
  expect(trace.type).toBe('heatmap')
  expect(trace.z).toEqual(MATRIX)
  expect(trace.x).toEqual(LABELS)
  expect(trace.y).toEqual(LABELS)
  expect(trace.colorscale).toBe('Viridis')
  expect(trace.zmin).toBe(-1)
  expect(trace.zmax).toBe(1)
  expect(titleText(figure())).toBe('Cosine similarity')
})

const PAIRS = [
  '#0 ↔ #1: 0.030',
  '#0 ↔ #3: 0.010',
  '#1 ↔ #3: -0.002',
  '#0 ↔ #2: -0.019',
  '#1 ↔ #2: -0.042',
]

test('lists the 5 most similar off-diagonal pairs, sorted desc, to 3 decimals', () => {
  renderMatrix()
  const lines = screen.getAllByText(/↔/)
  expect(lines).toHaveLength(5)
  for (const [i, line] of PAIRS.entries()) {
    expect(lines[i]).toHaveTextContent(line)
  }
  expect(screen.queryByText(/#2 ↔ #3/)).toBeNull()
})

test('shows "No vectors" when the matrix is empty', () => {
  renderMatrix({ matrix: [], labels: [] })
  expect(screen.getByText('No vectors')).toBeInTheDocument()
  expect(screen.queryByTestId('plot')).toBeNull()
})
