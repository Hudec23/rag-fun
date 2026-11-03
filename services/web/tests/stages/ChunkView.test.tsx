// F-chunk (UI) — ChunkView
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import type { ChunkArtifact } from '../../src/api/types'
import { ChunkView } from '../../src/components/stages/ChunkView'
import { CHUNK } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

// Same artifact with a multi-level section path on chunk 0, so the ' › ' join is visible.
const DEEP: ChunkArtifact = {
  ...CHUNK,
  chunks: [
    { ...CHUNK.chunks[0], section_path: ['Q3 Report', 'Revenue', 'Subscriptions'] },
    ...CHUNK.chunks.slice(1),
  ],
}

// Same artifact with the semantic strategy and gaps between sentences.
const SEMANTIC: ChunkArtifact = {
  ...CHUNK,
  strategy: 'semantic',
  params: { strategy: 'semantic', breakpoint_percentile: 90, min_sentences: 2, max_sentences: 20 },
  semantic: {
    threshold: 0.35,
    gaps: [
      { after_sentence: 3, distance: 0.412, is_break: true },
      { after_sentence: 7, distance: 0.208, is_break: false },
      { after_sentence: 12, distance: 0.377, is_break: true },
    ],
  },
}

test('header shows 4 chunks · 74–132 chars · mean 102.5 and recursive', () => {
  renderWithProviders(<ChunkView stageRunId="sr2" artifact={CHUNK} />)
  expect(screen.getByText('4 chunks · 74–132 chars · mean 102.5')).toBeInTheDocument()
  expect(screen.getByText('recursive')).toBeInTheDocument()
  expect(screen.queryByRole('tab', { name: 'Breakpoints' })).toBeNull()
})

test('tabs Source / Cards / Histogram; cards show #0 and section path joined by ›', async () => {
  const user = userEvent.setup()
  renderWithProviders(<ChunkView stageRunId="sr2" artifact={DEEP} />)
  expect(screen.getByRole('tab', { name: 'Source' })).toBeInTheDocument()
  expect(screen.getByRole('tab', { name: 'Cards' })).toBeInTheDocument()
  expect(screen.getByRole('tab', { name: 'Histogram' })).toBeInTheDocument()
  await user.click(screen.getByRole('tab', { name: 'Cards' }))
  expect(screen.getByText('#0')).toBeInTheDocument()
  expect(screen.getByText('#1')).toBeInTheDocument()
  expect(screen.getByText('#2')).toBeInTheDocument()
  expect(screen.getByText('#3')).toBeInTheDocument()
  expect(screen.getByText('Q3 Report › Revenue › Subscriptions')).toBeInTheDocument()
})

test('semantic artifact adds a Breakpoints tab with 3-decimal distances and ✂ markers', async () => {
  const user = userEvent.setup()
  renderWithProviders(<ChunkView stageRunId="sr2" artifact={SEMANTIC} />)
  const tab = screen.getByRole('tab', { name: 'Breakpoints' })
  expect(tab).toBeInTheDocument()
  await user.click(tab)
  expect(screen.getByText('0.412')).toBeInTheDocument()
  expect(screen.getByText('0.208')).toBeInTheDocument()
  expect(screen.getByText('0.377')).toBeInTheDocument()
  expect(screen.getAllByText('✂')).toHaveLength(2)
})
