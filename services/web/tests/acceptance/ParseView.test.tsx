// F-parse (UI)
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { ParseView } from '../../src/components/stages/ParseView'
import { PARSE } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

test('parse view draws boxes on the page and syncs the selection', async () => {
  const user = userEvent.setup()
  renderWithProviders(<ParseView stageRunId="sr1" artifact={PARSE} />)
  expect(screen.getByText('2 pages · 8 elements · 0 tables')).toBeInTheDocument()
  const boxes = screen.getAllByTestId('bbox')
  expect(boxes).toHaveLength(5) // page 1
  expect(screen.getByAltText('page')).toHaveAttribute('src', '/api/v1/stage-runs/sr1/pages/1')
  await user.click(boxes[1])
  expect(boxes[1]).toHaveAttribute('data-element-id', 'e-0001')
})
