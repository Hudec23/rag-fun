import type { GenerateArtifact } from '../api/types'

export interface TokenBudgetBarProps {
  budget: GenerateArtifact['budget']
}

/**
 * Stacked horizontal bar of max_context_tokens: system (grey), question (blue), context (green), free
 * (white). Each segment has data-testid="seg-<name>" and width % of max. Text "<used total> /
 * <max_context_tokens> tokens (approx.) · <chunks_included> chunks included, <chunks_dropped>
 * dropped" where used total = system + question + used_context.
 */
export function TokenBudgetBar(_props: TokenBudgetBarProps): React.ReactElement {
  throw new Error('not implemented')
}
