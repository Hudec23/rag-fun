// F-embed (UI) — ScatterPlot
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { ScatterPlot } from '../../src/viz/ScatterPlot'
import { renderWithProviders } from '../setup/render'

const POINTS2D = [
  [0.1, 0.2],
  [0.3, 0.4],
  [0.5, 0.6],
  [0.7, 0.8],
]
const POINTS3D = [
  [0.1, 0.2, 0.3],
  [0.3, 0.4, 0.5],
  [0.5, 0.6, 0.7],
  [0.7, 0.8, 0.9],
]
const LABELS = ['one', 'two', 'three', 'four']
const GROUPS = ['a', 'a', 'b', 'b']

function renderScatter(overrides: Partial<Parameters<typeof ScatterPlot>[0]> = {}) {
  return renderWithProviders(
    <ScatterPlot
      points2d={POINTS2D}
      points3d={POINTS3D}
      labels={LABELS}
      groups={GROUPS}
      method="pca"
      {...overrides}
    />,
  )
}

function figure() {
  return JSON.parse(screen.getByTestId('plot').getAttribute('data-figure')!)
}

function titleText(fig: unknown): string {
  const title = (fig as { layout?: { title?: string | { text?: string } } }).layout?.title
  return typeof title === 'string' ? title : (title?.text ?? '')
}

test('renders one scatter trace per group with the 2D points', () => {
  renderScatter()
  const fig = figure()
  expect(fig.data).toHaveLength(2)
  expect(fig.data[0].name).toBe('a')
  expect(fig.data[1].name).toBe('b')
  expect(fig.data[0].type).toBe('scatter')
  expect(fig.data[1].type).toBe('scatter')
  expect(fig.data[0].x).toEqual([0.1, 0.3])
  expect(fig.data[0].y).toEqual([0.2, 0.4])
  expect(fig.data[1].x).toEqual([0.5, 0.7])
  expect(fig.data[1].y).toEqual([0.6, 0.8])
  expect(titleText(fig)).toContain('PCA projection')
})

test('switches to scatter3d traces when the 3D button is clicked', async () => {
  const user = userEvent.setup()
  renderScatter()
  await user.click(screen.getByRole('button', { name: '3D' }))
  const fig = figure()
  expect(fig.data).toHaveLength(2)
  expect(fig.data[0].name).toBe('a')
  expect(fig.data[1].name).toBe('b')
  expect(fig.data[0].type).toBe('scatter3d')
  expect(fig.data[1].type).toBe('scatter3d')
  expect(fig.data[0].z).toEqual([0.3, 0.5])
})

test('shows "Not enough chunks for UMAP 2D" when points2d is null and method is umap', () => {
  renderScatter({ method: 'umap', points2d: null })
  expect(screen.getByText('Not enough chunks for UMAP 2D')).toBeInTheDocument()
  expect(screen.queryByTestId('plot')).toBeNull()
})

test('sets the hover text of each trace to its labels', () => {
  renderScatter()
  const fig = figure()
  expect(fig.data[0].text).toEqual(['one', 'two'])
  expect(fig.data[1].text).toEqual(['three', 'four'])
})
