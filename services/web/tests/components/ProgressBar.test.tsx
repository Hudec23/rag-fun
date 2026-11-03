// ProgressBar (F-stage-flow): done/total text, aria values, fill width % (0 when total ≤ 0, max 100),
// optional message.
import { screen } from '@testing-library/react'

import { ProgressBar } from '../../src/components/ProgressBar'
import { renderWithProviders } from '../setup/render'

test('shows aria values, done/total text and a 25% width for done 1 total 4', () => {
  const { container } = renderWithProviders(<ProgressBar done={1} total={4} />)
  const bar = screen.getByRole('progressbar')
  expect(bar).toHaveAttribute('aria-valuenow', '1')
  expect(bar).toHaveAttribute('aria-valuemax', '4')
  expect(screen.getByText('1/4')).toBeInTheDocument()
  const fill = container.querySelector('[style*="width"]')
  expect(fill).not.toBeNull()
  expect(fill).toHaveStyle('width: 25%')
})

test('shows 0% width when total is 0', () => {
  const { container } = renderWithProviders(<ProgressBar done={0} total={0} />)
  const fill = container.querySelector('[style*="width"]')
  expect(fill).not.toBeNull()
  expect(fill).toHaveStyle('width: 0%')
})

test('caps width at 100% when done exceeds total', () => {
  const { container } = renderWithProviders(<ProgressBar done={9} total={4} />)
  const fill = container.querySelector('[style*="width"]')
  expect(fill).not.toBeNull()
  expect(fill).toHaveStyle('width: 100%')
})

test('shows the message when given', () => {
  renderWithProviders(<ProgressBar done={1} total={4} message="Processing chunks" />)
  expect(screen.getByText('Processing chunks')).toBeInTheDocument()
})
