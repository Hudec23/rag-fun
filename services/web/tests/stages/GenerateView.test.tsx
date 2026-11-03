// F-generate (UI) — GenerateView
import { screen } from '@testing-library/react'

import { GenerateView } from '../../src/components/stages/GenerateView'
import { GENERATE } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

test('renders the TokenBudgetBar and the answer with citation buttons', () => {
  renderWithProviders(<GenerateView stageRunId="sr8" artifact={GENERATE} />)
  // used = 60 system + 8 question + 75 context
  expect(
    screen.getByText('143 / 4000 tokens (approx.) · 2 chunks included, 1 dropped'),
  ).toBeInTheDocument()
  expect(screen.getByTestId('seg-system')).toBeInTheDocument()
  expect(screen.getByTestId('seg-question')).toBeInTheDocument()
  expect(screen.getByTestId('seg-context')).toBeInTheDocument()
  expect(screen.getByTestId('seg-free')).toBeInTheDocument()
  // one button per [n] marker in the answer; [2] is cited twice
  expect(screen.getByRole('button', { name: '[1]' })).toBeInTheDocument()
  expect(screen.getAllByRole('button', { name: '[2]' })).toHaveLength(2)
  // plain answer text stays readable between the citation buttons
  expect(screen.getByText(/should continue in Q4/)).toBeInTheDocument()
  // context list: one entry per included chunk
  expect(screen.getAllByText(/q3-report\.pdf/)).toHaveLength(2)
})

test("liveText 'Revenue gr' replaces the answer while streaming", () => {
  renderWithProviders(<GenerateView stageRunId="sr8" artifact={GENERATE} liveText="Revenue gr" />)
  expect(screen.getByText('Revenue gr')).toBeInTheDocument()
  // streaming=true → blinking cursor after the live text
  expect(screen.getByText('▌')).toBeInTheDocument()
  // final answer and its citation buttons are gone while streaming
  expect(screen.queryByText(/should continue in Q4/)).toBeNull()
  expect(screen.queryByRole('button', { name: '[1]' })).toBeNull()
  expect(screen.queryByRole('button', { name: '[2]' })).toBeNull()
  // budget bar is unaffected by streaming
  expect(
    screen.getByText('143 / 4000 tokens (approx.) · 2 chunks included, 1 dropped'),
  ).toBeInTheDocument()
})

test("footer shows 'ollama · qwen3:8b' and '210 prompt / 18 completion tokens'", () => {
  renderWithProviders(<GenerateView stageRunId="sr8" artifact={GENERATE} />)
  expect(screen.getByText('ollama · qwen3:8b')).toBeInTheDocument()
  expect(screen.getByText('210 prompt / 18 completion tokens')).toBeInTheDocument()
})
