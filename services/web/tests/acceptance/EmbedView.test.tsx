// F-embed (UI)
import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { EmbedView } from '../../src/components/stages/EmbedView'
import { CHUNK, EMBED } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

test('embed view shows tokens, over-limit and projection', async () => {
  const user = userEvent.setup()
  renderWithProviders(<EmbedView stageRunId="sr3" artifact={EMBED} chunks={CHUNK.chunks} />)
  expect(screen.getByText(/1 over limit/)).toBeInTheDocument()
  expect(screen.getByText(/Vectors are not stored yet/)).toBeInTheDocument()
  await user.click(screen.getByRole('tab', { name: 'Projection' }))
  const fig = JSON.parse(screen.getByTestId('plot').getAttribute('data-figure')!)
  expect(fig.data[0].type).toBe('scatter')
  await user.click(screen.getByRole('button', { name: 'UMAP' }))
  expect(screen.getByText('Not enough chunks for UMAP 2D')).toBeInTheDocument()
  await user.click(screen.getByRole('tab', { name: 'Similarity' }))
  expect(within(screen.getByRole('tabpanel')).getAllByText(/↔/)).toHaveLength(5)
})
