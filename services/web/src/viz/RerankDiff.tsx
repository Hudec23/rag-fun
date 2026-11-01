import type { RerankArtifact } from '../api/types'

export interface RerankDiffProps {
  artifact: RerankArtifact
}

/**
 * Two columns "Before" (artifact.before) and "After" (artifact.after[].hit). After rows show
 * "↑3" (green) / "↓2" (red) / "=" from previous_rank − new rank, plus rerank_score (4 decimals) or "—".
 * disabled → banner "Reranking disabled — showing retrieval order".
 */
export function RerankDiff(_props: RerankDiffProps): React.ReactElement {
  throw new Error('not implemented')
}
