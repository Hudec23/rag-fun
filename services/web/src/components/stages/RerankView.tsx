import type { RerankArtifact } from '../../api/types'
import { RerankDiff } from '../../viz/RerankDiff'

export interface RerankViewProps {
  stageRunId: string
  artifact: RerankArtifact
}

/**
 * Header "<model> · top <top_n>" (or disabled banner via RerankDiff) then <RerankDiff>.
 */
export function RerankView({ artifact }: RerankViewProps): React.ReactElement {
  return (
    <section className="flex flex-col gap-3 p-4">
      {artifact.model !== null ? (
        <header className="text-sm">
          <span>{`${artifact.model} · top ${artifact.top_n}`}</span>
        </header>
      ) : null}
      <RerankDiff artifact={artifact} />
    </section>
  )
}
