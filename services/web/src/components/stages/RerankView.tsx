import type { RerankArtifact } from '../../api/types'

export interface RerankViewProps {
  stageRunId: string
  artifact: RerankArtifact
}

/**
 * Header "<model> · top <top_n>" (or disabled banner via RerankDiff) then <RerankDiff>.
 */
export function RerankView(_props: RerankViewProps): React.ReactElement {
  throw new Error('not implemented')
}
