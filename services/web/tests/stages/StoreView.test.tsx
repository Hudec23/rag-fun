// F-store (UI) — StoreView
import { screen } from '@testing-library/react'

import type { StoreArtifact } from '../../src/api/types'
import { StoreView } from '../../src/components/stages/StoreView'
import { COLLECTION, STORE } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

// Same artifact after a re-ingest that replaced old points.
const REWRITTEN: StoreArtifact = { ...STORE, points_deleted: 12 }

test('4 points written to rf_019a4b2c1d007b0080000000000000aa', () => {
  renderWithProviders(<StoreView stageRunId="sr4" artifact={STORE} collectionId={COLLECTION.id} />)
  expect(
    screen.getByText('4 points written to rf_019a4b2c1d007b0080000000000000aa'),
  ).toBeInTheDocument()
  expect(screen.queryByText(/old points replaced/)).toBeNull()
})

test('vector config table shows text-dense 384 Cosine and text-sparse idf', () => {
  renderWithProviders(<StoreView stageRunId="sr4" artifact={STORE} collectionId={COLLECTION.id} />)
  expect(screen.getByText('text-dense')).toBeInTheDocument()
  expect(screen.getByText('384')).toBeInTheDocument()
  expect(screen.getByText('Cosine')).toBeInTheDocument()
  expect(screen.getByText('text-sparse')).toBeInTheDocument()
  expect(screen.getByText('idf')).toBeInTheDocument()
})

test("payload sample <pre> contains 'meta'", () => {
  const { container } = renderWithProviders(
    <StoreView stageRunId="sr4" artifact={STORE} collectionId={COLLECTION.id} />,
  )
  const pre = container.querySelector('pre')
  expect(pre).not.toBeNull()
  expect(pre!.textContent).toContain('meta')
})

test('points_deleted > 0 → 12 old points replaced', () => {
  renderWithProviders(
    <StoreView stageRunId="sr4" artifact={REWRITTEN} collectionId={COLLECTION.id} />,
  )
  expect(screen.getByText(/12 old points replaced/)).toBeInTheDocument()
})
