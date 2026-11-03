// F-chunk (UI) — ChunkHighlighter
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'

import type { ChunkArtifact } from '../../src/api/types'
import { ChunkHighlighter } from '../../src/viz/ChunkHighlighter'
import { CHUNK } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

type Chunk = ChunkArtifact['chunks'][number]

function mkChunk(
  index: number,
  char_start: number | null,
  char_end: number | null,
  text: string,
): Chunk {
  return {
    index,
    doc_id: `019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a01:${String(index).padStart(5, '0')}`,
    text,
    char_start,
    char_end,
    element_ids: [],
    page_numbers: [],
    section_path: [],
    element_type: 'text',
    char_count: text.length,
    token_estimate: 0,
  }
}

test('marks the chunk 0/1 overlap span with data-overlap and its covering indices', () => {
  const { container } = renderWithProviders(
    <ChunkHighlighter sourceText={CHUNK.source_text} chunks={CHUNK.chunks} />,
  )
  const overlap = container.querySelector('[data-chunks="0,1"]')
  expect(overlap).not.toBeNull()
  expect(overlap).toHaveAttribute('data-overlap', 'true')
})

test('concatenates the segment spans to the full source text', () => {
  const { container } = renderWithProviders(
    <ChunkHighlighter sourceText={CHUNK.source_text} chunks={CHUNK.chunks} />,
  )
  const spans = Array.from(container.querySelectorAll('span[data-chunks]'))
  expect(spans.length).toBeGreaterThan(0)
  expect(spans.map((span) => span.textContent ?? '').join('')).toBe(CHUNK.source_text)
})

test('clicking a span covered by chunks 1 and 2 selects the lowest covering index', async () => {
  const sourceText = 'ABCDEFGHIJKLMNOPQRSTUVWX'
  const chunks = [
    mkChunk(0, 0, 5, 'ABCDE'),
    mkChunk(1, 5, 20, 'FGHIJKLMNOPQRSTU'),
    mkChunk(2, 10, 24, 'KLMNOPQRSTUVWX'),
  ]
  const onSelect = vi.fn()
  const user = userEvent.setup()
  const { container } = renderWithProviders(
    <ChunkHighlighter sourceText={sourceText} chunks={chunks} onSelect={onSelect} />,
  )
  const spans = container.querySelectorAll('[data-chunks="1,2"]')
  expect(spans).toHaveLength(1)
  await user.click(spans[0])
  expect(onSelect).toHaveBeenCalledTimes(1)
  expect(onSelect).toHaveBeenCalledWith(1)
})

test('lists chunks without a source position under their own section', () => {
  const sourceText = 'The quick brown fox jumps over the lazy dog near the river bank at dawn.'
  const chunks = [
    mkChunk(0, 0, 19, 'The quick brown fox'),
    mkChunk(1, null, null, 'NOPOS-CHUNK-XYZ'),
  ]
  renderWithProviders(<ChunkHighlighter sourceText={sourceText} chunks={chunks} />)
  expect(screen.getByText('Chunks without a source position')).toBeInTheDocument()
  expect(screen.getByText('NOPOS-CHUNK-XYZ')).toBeInTheDocument()
})
