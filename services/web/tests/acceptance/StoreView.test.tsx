// F-store (UI)
import { screen } from '@testing-library/react'

import { StoreView } from '../../src/components/stages/StoreView'
import { COLLECTION, STORE } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

test('store view summarises what was written', () => {
  renderWithProviders(<StoreView stageRunId="sr4" artifact={STORE} collectionId={COLLECTION.id} />)
  expect(
    screen.getByText('4 points written to rf_019a4b2c1d007b0080000000000000aa'),
  ).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Open in Qdrant browser' })).toHaveAttribute(
    'href',
    `/qdrant/${COLLECTION.id}`,
  )
})
