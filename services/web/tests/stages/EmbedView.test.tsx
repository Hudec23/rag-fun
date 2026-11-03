// F-embed (UI) — EmbedView
import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { EmbedView } from '../../src/components/stages/EmbedView'
import { CHUNK, EMBED } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

test("'4 chunks · all-minilm (384d) · Qdrant/bm25' and '1 over limit'", () => {
  renderWithProviders(<EmbedView stageRunId="sr3" artifact={EMBED} chunks={CHUNK.chunks} />)
  expect(screen.getByText('4 chunks · all-minilm (384d) · Qdrant/bm25')).toBeInTheDocument()
  expect(screen.getByText('1 over limit')).toBeInTheDocument()
  expect(
    screen.getByText('Vectors are not stored yet — run Store to write them to Qdrant.'),
  ).toBeInTheDocument()
})

test('Tokens tab: chunk selector switches TokenView', async () => {
  const user = userEvent.setup()
  renderWithProviders(<EmbedView stageRunId="sr3" artifact={EMBED} chunks={CHUNK.chunks} />)
  await user.click(screen.getByRole('tab', { name: 'Tokens' }))
  const panel = screen.getByRole('tabpanel')
  expect(within(panel).getByText('22 / 256 tokens')).toBeInTheDocument()
  expect(within(panel).getByText('q3')).toBeInTheDocument()
  expect(within(panel).getByText('report')).toBeInTheDocument()
  expect(within(panel).getByText('showing first 14')).toBeInTheDocument()
  const select = screen.getByRole('combobox')
  await user.selectOptions(select, within(select).getAllByRole('option')[3])
  expect(within(panel).getByText('300 / 256 tokens')).toBeInTheDocument()
  expect(within(panel).getByText('over limit — truncated by the model')).toBeInTheDocument()
  expect(within(panel).getByText('showing first 22')).toBeInTheDocument()
  expect(within(panel).queryByText('q3')).toBeNull()
  expect(within(panel).getByText('dividend')).toBeInTheDocument()
})

test('Projection tab PCA uses projections.pca2; UMAP null → not-enough message', async () => {
  const user = userEvent.setup()
  renderWithProviders(<EmbedView stageRunId="sr3" artifact={EMBED} chunks={CHUNK.chunks} />)
  await user.click(screen.getByRole('tab', { name: 'Projection' }))
  const fig = JSON.parse(screen.getByTestId('plot').getAttribute('data-figure')!)
  expect(fig.data).toHaveLength(1)
  expect(fig.data[0].type).toBe('scatter')
  expect(fig.data[0].name).toBe('text')
  expect(fig.data[0].x).toEqual([0.797358, -0.824419, 0.691042, -0.305149])
  expect(fig.data[0].y).toEqual([-0.109778, 0.363859, -0.360824, -0.870122])
  expect(fig.layout.title).toBe('PCA projection')
  await user.click(screen.getByRole('button', { name: 'UMAP' }))
  expect(screen.getByText('Not enough chunks for UMAP 2D')).toBeInTheDocument()
  expect(screen.queryByTestId('plot')).toBeNull()
})

test('Similarity tab renders SimilarityMatrix', async () => {
  const user = userEvent.setup()
  renderWithProviders(<EmbedView stageRunId="sr3" artifact={EMBED} chunks={CHUNK.chunks} />)
  await user.click(screen.getByRole('tab', { name: 'Similarity' }))
  const fig = JSON.parse(screen.getByTestId('plot').getAttribute('data-figure')!)
  expect(fig.data[0].type).toBe('heatmap')
  expect(fig.data[0].z).toEqual(EMBED.similarity)
  expect(fig.data[0].x).toEqual(['#0', '#1', '#2', '#3'])
  expect(fig.layout.title).toBe('Cosine similarity')
  const panel = screen.getByRole('tabpanel')
  expect(within(panel).getAllByText(/↔/)).toHaveLength(5)
  expect(within(panel).getByText('#0 ↔ #1: 0.030')).toBeInTheDocument()
  expect(within(panel).getByText('#0 ↔ #3: 0.010')).toBeInTheDocument()
  expect(within(panel).getByText('#1 ↔ #3: -0.002')).toBeInTheDocument()
  expect(within(panel).getByText('#0 ↔ #2: -0.019')).toBeInTheDocument()
  expect(within(panel).getByText('#1 ↔ #2: -0.042')).toBeInTheDocument()
})
