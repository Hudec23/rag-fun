// F-rerank (UI) — RerankDiff
import { screen } from '@testing-library/react'

import type { RerankArtifact } from '../../src/api/types'
import { RerankDiff } from '../../src/viz/RerankDiff'
import { RERANK } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

// The innermost element whose text matches `marker`, walked up to the first ancestor that
// carries a rank delta (↑/↓/=) — the After row it lives in.
function afterRow(marker: RegExp): Element {
  const el = screen
    .getAllByText(marker)
    .reduce((min, cur) =>
      (cur.textContent ?? '').length < (min.textContent ?? '').length ? cur : min,
    )
  let row: Element = el
  while (row.parentElement && !/[↑↓=]/.test(row.textContent ?? '')) row = row.parentElement
  return row
}

test('RERANK fixture: after row 1 shows ↑1 (previous 2 → 1), row 2 ↓1, row 3 ↑1', () => {
  renderWithProviders(<RerankDiff artifact={RERANK} />)
  expect(screen.getByText('Before')).toBeInTheDocument()
  expect(screen.getByText('After')).toBeInTheDocument()
  // row 1: the reranked hit (score 0.9700) moved from previous rank 2 to 1
  expect(afterRow(/0\.9700/)).toHaveTextContent('↑1')
  // row 2: previous rank 1 → 2
  expect(afterRow(/0\.8800/)).toHaveTextContent('↓1')
  // row 3: previous rank 4 → 3
  expect(afterRow(/0\.1200/)).toHaveTextContent('↑1')
  expect(screen.getAllByText('↑1')).toHaveLength(2)
  expect(screen.getByText('↓1')).toBeInTheDocument()
})

test('shows rerank_score with 4 decimals (0.97 → 0.9700), and — when it is null', () => {
  const mounted = renderWithProviders(<RerankDiff artifact={RERANK} />)
  expect(screen.getByText('0.9700')).toBeInTheDocument()
  expect(screen.getByText('0.8800')).toBeInTheDocument()
  mounted.unmount()

  const artifact: RerankArtifact = {
    ...RERANK,
    after: RERANK.after.map((entry) => ({ ...entry, rerank_score: null })),
  }
  renderWithProviders(<RerankDiff artifact={artifact} />)
  expect(screen.getAllByText('—')).toHaveLength(3)
  expect(screen.queryByText('0.9700')).not.toBeInTheDocument()
})

test('enabled false shows the banner "Reranking disabled — showing retrieval order"', () => {
  const artifact: RerankArtifact = { ...RERANK, enabled: false }
  renderWithProviders(<RerankDiff artifact={artifact} />)
  expect(screen.getByText('Reranking disabled — showing retrieval order')).toBeInTheDocument()
})
