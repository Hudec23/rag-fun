// F-retrieve (UI) — HybridLists
import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import type { RetrieveArtifact } from '../../src/api/types'
import { HybridLists } from '../../src/viz/HybridLists'
import { RETRIEVE } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

// The innermost element whose text matches `marker`, walked up to its highlighted row.
function row(marker: RegExp): HTMLElement {
  const el = screen
    .getAllByText(marker)
    .reduce((min, cur) =>
      (cur.textContent ?? '').length < (min.textContent ?? '').length ? cur : min,
    )
  return el.closest<HTMLElement>('[data-highlighted]') ?? el
}

test('shows the Dense, Sparse and Fused (RRF) columns with the fused first row tagged D#1 S#2', () => {
  renderWithProviders(<HybridLists artifact={RETRIEVE} />)
  for (const col of ['Dense', 'Sparse', 'Fused (RRF)'])
    expect(screen.getByText(col)).toBeInTheDocument()
  expect(screen.getAllByText('D#1 S#2').length).toBeGreaterThan(0)
  // a query selector only appears with more than one per_query entry
  expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
})

test('omits the Dense column when the dense list is null', () => {
  const artifact: RetrieveArtifact = {
    ...RETRIEVE,
    mode: 'sparse',
    per_query: [
      {
        query: RETRIEVE.per_query[0].query,
        dense: null,
        sparse: RETRIEVE.per_query[0].sparse,
      },
    ],
  }
  renderWithProviders(<HybridLists artifact={artifact} />)
  expect(screen.queryByText('Dense')).not.toBeInTheDocument()
  expect(screen.getByText('Sparse')).toBeInTheDocument()
  expect(screen.getByText('Fused (RRF)')).toBeInTheDocument()
})

test('highlights every row with the same doc_id when a dense row is clicked', async () => {
  const user = userEvent.setup()
  renderWithProviders(<HybridLists artifact={RETRIEVE} />)
  // doc ...:00001 is dense #1, sparse #2 and fused #1; first 'headcount' in DOM order is the dense row
  await user.click(screen.getAllByText(/headcount/)[0])
  expect(row(/0\.8100/)).toHaveAttribute('data-highlighted', 'true') // dense #1
  expect(row(/5\.1000/)).toHaveAttribute('data-highlighted', 'true') // sparse #2
  expect(row(/D#1 S#2/)).toHaveAttribute('data-highlighted', 'true') // fused #1
  expect(row(/0\.6200/)).not.toHaveAttribute('data-highlighted', 'true') // dense #2, other doc
})

test('offers a query selector and switches to the second query lists on select', async () => {
  const user = userEvent.setup()
  const [firstHit] = RETRIEVE.per_query[0].dense ?? []
  const artifact: RetrieveArtifact = {
    ...RETRIEVE,
    per_query: [
      RETRIEVE.per_query[0],
      {
        query: 'Why did costs rise?',
        dense: [
          {
            ...firstHit,
            point_id: '00000000000000000000000000000090',
            doc_id: '019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a01:90001',
            rank: 1,
            score: 0.77,
            content: 'Salaries and hiring costs rose sharply in Q4.',
          },
        ],
        sparse: null,
      },
    ],
  }
  renderWithProviders(<HybridLists artifact={artifact} />)
  const select = screen.getByRole('combobox')
  expect(within(select).getAllByRole('option')).toHaveLength(2)
  await user.selectOptions(
    select,
    within(select).getByRole('option', { name: /Why did costs rise/ }),
  )
  expect(await screen.findByText(/0\.7700/)).toBeInTheDocument()
  expect(screen.queryByText(/0\.8100/)).not.toBeInTheDocument()
})
