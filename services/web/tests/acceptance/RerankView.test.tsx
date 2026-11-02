// F-rerank (UI)
import { screen } from '@testing-library/react'

import { RerankView } from '../../src/components/stages/RerankView'
import { RERANK } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

test('rerank view shows rank movement', () => {
  renderWithProviders(<RerankView stageRunId="k" artifact={RERANK} />)
  expect(screen.getAllByText('↑1')).toHaveLength(2)
  expect(screen.getByText('↓1')).toBeInTheDocument()
  expect(screen.getByText('0.9700')).toBeInTheDocument()
})
