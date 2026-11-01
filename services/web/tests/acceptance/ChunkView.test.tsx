// F-chunk (UI)
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { ChunkView } from '../../src/components/stages/ChunkView'
import { CHUNK } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

test('chunk view highlights overlap and shows stats', async () => {
  const user = userEvent.setup()
  renderWithProviders(<ChunkView stageRunId="sr2" artifact={CHUNK} />)
  expect(screen.getByText(/4 chunks/)).toBeInTheDocument()
  expect(document.querySelector('[data-overlap="true"]')).not.toBeNull()
  await user.click(screen.getByRole('tab', { name: 'Histogram' }))
  expect(screen.getByTestId('plot')).toBeInTheDocument()
})
