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
export function TransformView({ artifact }: TransformViewProps): React.ReactElement {
  const { strategy, question, queries, hyde_document, messages, model } = artifact

  return (
    <section className="flex flex-col gap-3 p-4">
      <header className="flex items-center gap-2 text-sm">
        <span className="rounded bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-800">
          {strategy}
        </span>
      </header>
      <div className="rounded border border-gray-200 bg-white p-3">
        <h3 className="mb-1 text-sm font-medium text-gray-700">Original question</h3>
        <p className="whitespace-pre-wrap break-words text-sm">{question}</p>
      </div>
      {strategy === 'none' ? (
        <p className="text-sm text-gray-500">No transformation — the question is used as is.</p>
      ) : strategy === 'hyde' ? (
        <div>
          <h3 className="mb-1 text-sm font-medium text-gray-700">Hypothetical document</h3>
          <blockquote className="border-l-4 border-gray-300 pl-3 text-sm text-gray-700">
            {hyde_document}
          </blockquote>
        </div>
      ) : (
        <div>
          <h3 className="mb-1 text-sm font-medium text-gray-700">Search queries</h3>
          <ul className="flex flex-col gap-1">
            {queries.map((query, index) => (
              <li
                key={index}
                className="rounded border border-gray-200 bg-white px-3 py-1.5 text-sm"
              >
                {query}
              </li>
            ))}
          </ul>
        </div>
      )}
      {messages.length > 0 ? (
        <details className="rounded border border-gray-200">
          <summary className="cursor-pointer px-3 py-2 text-sm font-medium text-gray-700">
            Prompt
          </summary>
          <div className="divide-y divide-gray-100 border-t border-gray-200">
            {messages.map((message, index) => (
              <div key={index} className="space-y-1 px-3 py-2">
                <span className="text-xs font-medium text-gray-500">{message.role}</span>
                <p className="whitespace-pre-line text-sm text-gray-700">{message.content}</p>
              </div>
            ))}
          </div>
        </details>
      ) : null}
      {model !== null ? (
        <footer className="text-xs text-gray-500">{`${model.provider} · ${model.model}`}</footer>
      ) : null}
    </section>
  )
}
