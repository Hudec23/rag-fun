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
export function TokenBudgetBar({ budget }: TokenBudgetBarProps): React.ReactElement {
  const max = budget.max_context_tokens
  const used = budget.system_tokens + budget.question_tokens + budget.used_context_tokens
  const scale = used > max && used > 0 ? max / used : 1
  const pct = (tokens: number) => (max > 0 ? (tokens / max) * 100 : 0) * scale
  const usedPct =
    pct(budget.system_tokens) + pct(budget.question_tokens) + pct(budget.used_context_tokens)
  const segments = [
    { name: 'system', width: pct(budget.system_tokens), className: 'bg-gray-300' },
    { name: 'question', width: pct(budget.question_tokens), className: 'bg-blue-500' },
    { name: 'context', width: pct(budget.used_context_tokens), className: 'bg-green-500' },
    { name: 'free', width: Math.max(0, 100 - usedPct), className: 'bg-white' },
  ]

  return (
    <section className="space-y-1">
      <div className="flex h-3 w-full overflow-hidden rounded border border-gray-200">
        {segments.map((segment) => (
          <div
            key={segment.name}
            data-testid={`seg-${segment.name}`}
            className={segment.className}
            style={{ width: `${segment.width}%` }}
          />
        ))}
      </div>
      <p className="text-sm text-gray-500">
        {`${used} / ${max} tokens (approx.) · ${budget.chunks_included} chunks included, ${budget.chunks_dropped} dropped`}
      </p>
    </section>
  )
}
