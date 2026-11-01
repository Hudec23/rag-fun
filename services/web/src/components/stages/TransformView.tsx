import type { TransformArtifact } from '../../api/types'

export interface TransformViewProps {
  stageRunId: string
  artifact: TransformArtifact
}

/**
 * Strategy name; "Original question" box; list "Search queries" (queries[]); for hyde the
 * hypothetical document in a quote block; collapsible "Prompt" showing messages (role + content).
 * strategy none → "No transformation — the question is used as is."
 */
export function TransformView(_props: TransformViewProps): React.ReactElement {
  throw new Error('not implemented')
}
