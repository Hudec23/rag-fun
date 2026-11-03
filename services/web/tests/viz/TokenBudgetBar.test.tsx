// F-generate (UI) — TokenBudgetBar
import { screen } from '@testing-library/react'

import { TokenBudgetBar } from '../../src/viz/TokenBudgetBar'
import { GENERATE } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

const SEGS = ['system', 'question', 'context', 'free']

function renderBudget(overrides: Partial<Parameters<typeof TokenBudgetBar>[0]> = {}) {
  return renderWithProviders(<TokenBudgetBar budget={GENERATE.budget} {...overrides} />)
}

function segmentWidth(name: string): number {
  return parseFloat(screen.getByTestId(`seg-${name}`).style.width)
}

test('shows the "143 / 4000 tokens (approx.) · 2 chunks included, 1 dropped" line', () => {
  renderBudget()
  expect(
    screen.getByText('143 / 4000 tokens (approx.) · 2 chunks included, 1 dropped'),
  ).toBeInTheDocument()
})

test('sizes seg-system 1.5%, seg-question 0.2%, seg-context 1.875% of max', () => {
  renderBudget()
  expect(segmentWidth('system')).toBeCloseTo(1.5, 6)
  expect(segmentWidth('question')).toBeCloseTo(0.2, 6)
  expect(segmentWidth('context')).toBeCloseTo(1.875, 6)
})

test('caps widths so the segments sum to 100% when used > max', () => {
  renderBudget({
    budget: {
      max_context_tokens: 100,
      system_tokens: 50,
      question_tokens: 30,
      used_context_tokens: 30,
      chunks_included: 3,
      chunks_dropped: 0,
    },
  })
  const total = SEGS.reduce((sum, name) => sum + segmentWidth(name), 0)
  expect(total).toBeGreaterThanOrEqual(99.9)
  expect(total).toBeLessThanOrEqual(100.1)
})
