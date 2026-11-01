import type { RetrieveArtifact } from '../../api/types'

export interface RetrieveViewProps {
  stageRunId: string
  artifact: RetrieveArtifact
}

/**
 * Header "<mode> · top_k <k> · RRF k <rrf_k>" and active filters as chips ("tags in finance");
 * then <HybridLists>.
 */
export function RetrieveView(_props: RetrieveViewProps): React.ReactElement {
  throw new Error('not implemented')
}
