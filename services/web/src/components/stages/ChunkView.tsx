import type { ChunkArtifact } from '../../api/types'

export interface ChunkViewProps {
  stageRunId: string
  artifact: ChunkArtifact
}

/**
 * Header: "<count> chunks · <min>–<max> chars · mean <mean>" + strategy name. Tabs are
 * <button role="tab"> (accessible name = label) above one <div role="tabpanel">: "Source"
 * (<ChunkHighlighter>), "Cards" (one card per chunk: #index, element_type badge, pages, section path
 * joined ' › ', text), "Histogram" (<LengthHistogram>). Semantic strategy: extra tab "Breakpoints"
 * listing gaps with distance (3 decimals) and a ✂ marker where is_break.
 */
export function ChunkView(_props: ChunkViewProps): React.ReactElement {
  throw new Error('not implemented')
}
