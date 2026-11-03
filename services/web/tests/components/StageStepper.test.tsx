// StageStepper (F-stage-flow): one button per stage with a status badge ("not run" when never
// run, else status + " v<version>"), aria-current on the selected step, onSelect on click,
// animate-pulse on running badges.
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'

import { StageStepper } from '../../src/components/StageStepper'
import { stageRun } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

test('shows badges done v2, stale v1, not run and failed v1 for the given stages', () => {
  renderWithProviders(
    <StageStepper
      stages={[
        { name: 'parse', run: stageRun('parse', { version: 2 }) },
        { name: 'chunk', run: stageRun('chunk', { status: 'stale' }) },
        { name: 'embed', run: null },
        { name: 'store', run: stageRun('store', { status: 'failed' }) },
      ]}
      selected="parse"
      onSelect={vi.fn()}
    />,
  )
  expect(screen.getByText('done v2')).toBeInTheDocument()
  expect(screen.getByText('stale v1')).toBeInTheDocument()
  expect(screen.getByText('not run')).toBeInTheDocument()
  expect(screen.getByText('failed v1')).toBeInTheDocument()
})

test('marks the selected chunk button with aria-current step', () => {
  renderWithProviders(
    <StageStepper
      stages={[
        { name: 'parse', run: stageRun('parse', { version: 2 }) },
        { name: 'chunk', run: stageRun('chunk', { status: 'stale' }) },
        { name: 'embed', run: null },
        { name: 'store', run: stageRun('store', { status: 'failed' }) },
      ]}
      selected="chunk"
      onSelect={vi.fn()}
    />,
  )
  expect(screen.getByRole('button', { name: /chunk/ })).toHaveAttribute('aria-current', 'step')
  expect(screen.getByRole('button', { name: /parse/ })).not.toHaveAttribute('aria-current')
})

test('calls onSelect with embed when the embed step is clicked', async () => {
  const onSelect = vi.fn()
  const user = userEvent.setup()
  renderWithProviders(
    <StageStepper
      stages={[
        { name: 'parse', run: stageRun('parse', { version: 2 }) },
        { name: 'chunk', run: stageRun('chunk', { status: 'stale' }) },
        { name: 'embed', run: null },
        { name: 'store', run: stageRun('store', { status: 'failed' }) },
      ]}
      selected="parse"
      onSelect={onSelect}
    />,
  )
  await user.click(screen.getByRole('button', { name: /embed/ }))
  expect(onSelect).toHaveBeenCalledTimes(1)
  expect(onSelect).toHaveBeenCalledWith('embed')
})

test('adds animate-pulse to the badge of a running stage', () => {
  renderWithProviders(
    <StageStepper
      stages={[
        { name: 'parse', run: stageRun('parse') },
        { name: 'chunk', run: stageRun('chunk', { status: 'running' }) },
      ]}
      selected="chunk"
      onSelect={vi.fn()}
    />,
  )
  expect(screen.getByText('running v1')).toHaveClass('animate-pulse')
})
