// F-rerank (UI) — RerankView
import { screen } from '@testing-library/react'

import type { RerankArtifact } from '../../src/api/types'
import { RerankView } from '../../src/components/stages/RerankView'
import { RERANK } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

// Same artifact with reranking turned off: no model, retrieval order kept.
const DISABLED: RerankArtifact = { ...RERANK, enabled: false, model: null }

test('header "Xenova/ms-marco-MiniLM-L-6-v2 · top 3"', () => {
  renderWithProviders(<RerankView stageRunId="sr1" artifact={RERANK} />)
  expect(screen.getByText('Xenova/ms-marco-MiniLM-L-6-v2 · top 3')).toBeInTheDocument()
})

test('renders RerankDiff rows', () => {
  renderWithProviders(<RerankView stageRunId="sr1" artifact={RERANK} />)
  expect(screen.getByText('Before')).toBeInTheDocument()
  expect(screen.getByText('After')).toBeInTheDocument()
  // before rows: retrieval scores with 4 decimals
  expect(screen.getAllByText('0.0325')).toHaveLength(2)
  expect(screen.getAllByText('0.0159')).toHaveLength(2)
  // after rows: rerank scores and rank movement
  expect(screen.getByText('0.9700')).toBeInTheDocument()
  expect(screen.getByText('0.8800')).toBeInTheDocument()
  expect(screen.getByText('0.1200')).toBeInTheDocument()
  expect(screen.getAllByText('↑1')).toHaveLength(2)
  expect(screen.getByText('↓1')).toBeInTheDocument()
})

test('disabled artifact shows the disabled banner', () => {
  renderWithProviders(<RerankView stageRunId="sr1" artifact={DISABLED} />)
  expect(screen.getByText('Reranking disabled — showing retrieval order')).toBeInTheDocument()
  expect(screen.queryByText('Xenova/ms-marco-MiniLM-L-6-v2 · top 3')).toBeNull()
})
