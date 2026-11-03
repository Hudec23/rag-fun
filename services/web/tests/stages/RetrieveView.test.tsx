// F-retrieve (UI) — RetrieveView
import { screen } from '@testing-library/react'

import { RetrieveView } from '../../src/components/stages/RetrieveView'
import { RETRIEVE } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

test('header "hybrid · top_k 10 · RRF k 60"', () => {
  renderWithProviders(<RetrieveView stageRunId="sr1" artifact={RETRIEVE} />)
  expect(screen.getByText('hybrid · top_k 10 · RRF k 60')).toBeInTheDocument()
})

test('filter chip "tags in finance"', () => {
  renderWithProviders(<RetrieveView stageRunId="sr1" artifact={RETRIEVE} />)
  expect(screen.getByText('tags in finance')).toBeInTheDocument()
})

test('renders HybridLists', () => {
  renderWithProviders(<RetrieveView stageRunId="sr1" artifact={RETRIEVE} />)
  expect(screen.getByText('Dense')).toBeInTheDocument()
  expect(screen.getByText('Sparse')).toBeInTheDocument()
  expect(screen.getByText('Fused (RRF)')).toBeInTheDocument()
  expect(screen.getByText('D#1 S#2')).toBeInTheDocument()
})
