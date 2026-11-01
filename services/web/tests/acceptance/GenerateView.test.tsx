// F-generate (UI)
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { GenerateView } from '../../src/components/stages/GenerateView'
import { GENERATE } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

test('generate view shows budget and clickable citations', async () => {
  const user = userEvent.setup()
  renderWithProviders(<GenerateView stageRunId="g" artifact={GENERATE} />)
  expect(
    screen.getByText(/143 \/ 4000 tokens \(approx\.\) · 2 chunks included, 1 dropped/),
  ).toBeInTheDocument()
  const cites = screen.getAllByRole('button', { name: '[2]' })
  await user.click(cites[0])
  expect(cites[0]).toHaveAttribute('aria-pressed', 'true')
})

test('generate view streams live text', () => {
  renderWithProviders(<GenerateView stageRunId="g" artifact={GENERATE} liveText="Revenue gr" />)
  expect(screen.getByText(/Revenue gr/)).toBeInTheDocument()
})
