import { CHUNK_COLORS } from '../lib/colors'
import type { ChunkArtifact } from '../api/types'

export interface ChunkHighlighterProps {
  sourceText: string
  chunks: ChunkArtifact['chunks']
  selectedIndex?: number | null
  onSelect?: (index: number) => void
}

/**
 * Renders sourceText as segments split at every chunk char_start/char_end boundary. Each segment's
 * background = CHUNK_COLORS[first covering chunk index % 10]; a segment covered by ≥2 chunks (overlap)
 * gets data-overlap="true" and a striped/darker style; uncovered segments plain. Each segment
 * <span data-chunks="0,1"> lists covering indices. Click → onSelect(lowest covering index). Chunks with
 * char_start null are listed below as "Chunks without a source position" cards.
 */
export function ChunkHighlighter({
  sourceText,
  chunks,
  selectedIndex,
  onSelect,
}: ChunkHighlighterProps): React.ReactElement {
  const length = sourceText.length
  // Chunks with a usable [char_start, char_end) span, clamped to the source text.
  const placed = chunks.flatMap((c) =>
    c.char_start !== null && c.char_end !== null
      ? [
          {
            index: c.index,
            start: Math.max(0, Math.min(c.char_start, length)),
            end: Math.max(0, Math.min(c.char_end, length)),
          },
        ]
      : [],
  )
  const marks = new Set<number>([0, length])
  for (const p of placed) {
    if (p.end > p.start) {
      marks.add(p.start)
      marks.add(p.end)
    }
  }
  const points = [...marks].sort((a, b) => a - b)
  const segments: { start: number; end: number; covering: number[] }[] = []
  for (let i = 0; i + 1 < points.length; i++) {
    const start = points[i]
    const end = points[i + 1]
    if (end <= start) continue
    // Every boundary is a chunk start/end, so a chunk covering the open segment covers it fully.
    const covering = placed.filter((p) => p.start <= start && p.end >= end).map((p) => p.index)
    segments.push({ start, end, covering })
  }
  const unplaced = chunks.filter((c) => c.char_start === null)
  return (
    <section className="flex flex-col gap-3 p-4">
      <p className="rounded border border-gray-200 bg-white p-3 text-sm leading-7">
        {segments.map((seg) => {
          const lowest = seg.covering[0]
          const overlap = seg.covering.length >= 2
          const selected = lowest !== undefined && lowest === selectedIndex
          return (
            <span
              key={`${seg.start}-${seg.end}`}
              data-chunks={seg.covering.join(',')}
              {...(overlap ? { 'data-overlap': 'true' } : {})}
              {...(selected ? { 'data-selected': 'true' } : {})}
              className={`rounded-sm px-0.5 ${
                lowest !== undefined ? 'cursor-pointer' : ''
              } ${selected ? 'ring-2 ring-blue-600' : ''}`}
              style={{
                backgroundColor: lowest !== undefined ? CHUNK_COLORS[lowest % 10] : undefined,
                backgroundImage: overlap
                  ? 'repeating-linear-gradient(45deg, rgba(0,0,0,0.12) 0 4px, transparent 4px 8px)'
                  : undefined,
              }}
              onClick={lowest !== undefined ? () => onSelect?.(lowest) : undefined}
            >
              {sourceText.slice(seg.start, seg.end)}
            </span>
          )
        })}
      </p>
      {unplaced.length > 0 ? (
        <div>
          <h2 className="mb-2 text-sm font-semibold">Chunks without a source position</h2>
          <ul className="flex flex-col gap-2">
            {unplaced.map((c) => (
              <li key={c.index} className="rounded border border-gray-200 bg-gray-50 p-3 text-sm">
                <span className="mr-2 font-mono text-xs text-gray-500">#{c.index}</span>
                {c.text}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  )
}
