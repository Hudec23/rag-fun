// F-generate (UI) — AnswerWithCitations
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { AnswerWithCitations } from '../../src/viz/AnswerWithCitations'
import type { AnswerWithCitationsProps } from '../../src/viz/AnswerWithCitations'
import { GENERATE } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

function renderAnswer(overrides: Partial<AnswerWithCitationsProps> = {}) {
  return renderWithProviders(
    <AnswerWithCitations
      answer="Revenue grew 12 percent"
      context={GENERATE.context}
      {...overrides}
    />,
  )
}

test('turns every [n] marker into one button per number', () => {
  renderAnswer({ answer: 'x [2] y [1, 2]' })
  const buttons = screen.getAllByRole('button')
  expect(buttons.map((button) => button.textContent)).toEqual(['[2]', '[1]', '[2]'])
})

test('clicking [1] sets aria-pressed and shows its chunk card with filename', async () => {
  const user = userEvent.setup()
  renderAnswer({ answer: 'x [1] y' })
  const cite = screen.getByRole('button', { name: '[1]' })
  await user.click(cite)
  expect(cite).toHaveAttribute('aria-pressed', 'true')
  expect(screen.getByText('q3-report.pdf')).toBeInTheDocument()
})

test('leaves an unknown [7] as plain text', () => {
  const { container } = renderAnswer({ answer: 'see [7] for details' })
  expect(screen.queryByRole('button', { name: '[7]' })).toBeNull()
  expect(container.textContent ?? '').toContain('see [7] for details')
})

test('shows a blinking cursor after the text while streaming', () => {
  const { container } = renderAnswer({ streaming: true })
  const cursor = container.querySelector('.animate-pulse')
  expect(cursor).not.toBeNull()
  const text = screen.getByText('Revenue grew 12 percent')
  // the cursor comes after the answer text, never before it
  expect(text.compareDocumentPosition(cursor!) & Node.DOCUMENT_POSITION_PRECEDING).toBe(0)
})

test('numbers the context list [1] and [2] below the answer', () => {
  const { container } = renderAnswer()
  expect(container.textContent ?? '').toContain('[1]')
  expect(container.textContent ?? '').toContain('[2]')
})
