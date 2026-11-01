import type { GenerateArtifact } from '../../api/types'

export interface GenerateViewProps {
  stageRunId: string
  artifact: GenerateArtifact
  liveText?: string | null
}

/**
 * <TokenBudgetBar>, then <AnswerWithCitations answer context>; while props.liveText is set
 * (streaming) render that text instead with streaming=true. Collapsible "Prompt" with messages.
 * Footer: provider/model and usage tokens when not null.
 */
export function GenerateView(_props: GenerateViewProps): React.ReactElement {
  throw new Error('not implemented')
}
