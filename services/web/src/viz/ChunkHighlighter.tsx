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
export function ChunkHighlighter(_props: ChunkHighlighterProps): React.ReactElement {
  throw new Error('not implemented')
}
