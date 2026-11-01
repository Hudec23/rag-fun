import type { StoreArtifact } from '../../api/types'

export interface StoreViewProps {
  stageRunId: string
  artifact: StoreArtifact
  collectionId?: string
}

/**
 * Summary: "<points_written> points written to <qdrant_collection>" (+ "<points_deleted> old
 * points replaced" when > 0). Vector config table (dense name/size/distance, sparse name/modifier).
 * Payload sample as pretty JSON (<pre>) with filterable keys (meta.*) highlighted. Link "Open in Qdrant
 * browser" → /qdrant/<collectionId>.
 */
export function StoreView(_props: StoreViewProps): React.ReactElement {
  throw new Error('not implemented')
}
