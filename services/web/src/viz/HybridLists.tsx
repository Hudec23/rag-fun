import type { RetrieveArtifact } from '../api/types'

export interface HybridListsProps {
  artifact: RetrieveArtifact
}

/**
 * Three columns for per_query[0] (with a query selector when per_query.length > 1): "Dense", "Sparse"
 * (column omitted when the list is null), "Fused (RRF)" from artifact.fused. Each row: rank, score (4
 * decimals), first 120 chars, filename + page. Hovering/clicking a row highlights the same doc_id in all
 * columns (data-highlighted="true"). Fused rows show source ranks as "D#2 S#5".
 */
export function HybridLists(_props: HybridListsProps): React.ReactElement {
  throw new Error('not implemented')
}
