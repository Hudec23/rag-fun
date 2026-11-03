// F-embed (UI) — TokenView
import { screen } from '@testing-library/react'

import { TokenView } from '../../src/viz/TokenView'
import { renderWithProviders } from '../setup/render'

function renderTokens(overrides: Partial<Parameters<typeof TokenView>[0]> = {}) {
  return renderWithProviders(
    <TokenView
      tokens={['[CLS]', 'hi', '[SEP]']}
      tokenCount={3}
      maxTokens={256}
      overLimit={false}
      {...overrides}
    />,
  )
}

test('renders 3 token pills in order with the "3 / 256 tokens" header', () => {
  renderTokens()
  const pills = screen.getAllByTestId('token')
  expect(pills).toHaveLength(3)
  expect(pills.map((pill) => pill.textContent)).toEqual(['[CLS]', 'hi', '[SEP]'])
  expect(screen.getByText('3 / 256 tokens')).toBeInTheDocument()
  expect(screen.queryByText(/over limit/)).toBeNull()
  expect(screen.queryByText(/showing first/)).toBeNull()
})

test('shows "over limit — truncated by the model" when overLimit', () => {
  renderTokens({ overLimit: true })
  expect(screen.getByText('over limit — truncated by the model')).toBeInTheDocument()
})

test('notes "showing first 2" when tokens.length < tokenCount', () => {
  renderTokens({ tokens: ['a', 'b'], tokenCount: 5000, maxTokens: 256 })
  expect(screen.getByText('showing first 2')).toBeInTheDocument()
  expect(screen.getByText('5000 / 256 tokens')).toBeInTheDocument()
})
