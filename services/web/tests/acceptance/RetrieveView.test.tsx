// F-retrieve (UI)
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { RetrieveView } from '../../src/components/stages/RetrieveView'
import { RETRIEVE } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

test('retrieve view shows dense, sparse and fused lists and cross-highlights', async () => {
  const user = userEvent.setup()
  renderWithProviders(<RetrieveView stageRunId="r" artifact={RETRIEVE} />)
  for (const col of ['Dense', 'Sparse', 'Fused (RRF)'])
    expect(screen.getByText(col)).toBeInTheDocument()
  expect(screen.getByText('hybrid · top_k 10 · RRF k 60')).toBeInTheDocument()
  expect(screen.getAllByText('D#1 S#2').length).toBeGreaterThan(0)
  const rows = screen.getAllByText(/Europe contributed/)
  await user.click(rows[0])
  expect(document.querySelectorAll('[data-highlighted="true"]').length).toBeGreaterThanOrEqual(2)
})
