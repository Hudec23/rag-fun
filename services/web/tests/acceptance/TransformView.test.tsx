// F-transform (UI)
import { screen } from '@testing-library/react'

import { TransformView } from '../../src/components/stages/TransformView'
import { TRANSFORM } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

test('transform view lists the generated queries', () => {
  renderWithProviders(<TransformView stageRunId="t" artifact={TRANSFORM} />)
  expect(screen.getByText('subscription revenue trend')).toBeInTheDocument()
  expect(screen.getByText('Search queries')).toBeInTheDocument()
})
