import type { GenerateArtifact } from '../../api/types'

import { AnswerWithCitations } from '../../viz/AnswerWithCitations'
import { TokenBudgetBar } from '../../viz/TokenBudgetBar'

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
export function GenerateView({ artifact, liveText }: GenerateViewProps): React.ReactElement {
  const usage = artifact.usage

  return (
    <section className="space-y-4">
      <TokenBudgetBar budget={artifact.budget} />
      <AnswerWithCitations
        answer={liveText != null ? liveText : artifact.answer}
        context={liveText != null ? [] : artifact.context}
        streaming={liveText != null}
      />
      <details className="rounded border border-gray-200">
        <summary className="cursor-pointer px-3 py-2 text-sm font-medium text-gray-700">
          Prompt
        </summary>
        <ul className="divide-y divide-gray-100 border-t border-gray-200">
          {artifact.messages.map((message, index) => (
            <li key={index} className="space-y-1 px-3 py-2">
              <span className="text-xs font-medium text-gray-500">{message.role}</span>
              <p className="whitespace-pre-line text-sm text-gray-700">{message.content}</p>
            </li>
          ))}
        </ul>
      </details>
      <footer className="flex items-baseline justify-between text-xs text-gray-500">
        <span>{`${artifact.model.provider} · ${artifact.model.model}`}</span>
        {usage.prompt_tokens !== null && usage.completion_tokens !== null ? (
          <span>{`${usage.prompt_tokens} prompt / ${usage.completion_tokens} completion tokens`}</span>
        ) : null}
      </footer>
    </section>
  )
}
