import { useState } from 'react'

import type { GenerateArtifact } from '../api/types'

export interface AnswerWithCitationsProps {
  answer: string
  context: GenerateArtifact['context']
  streaming?: boolean
}

type CtxEntry = GenerateArtifact['context'][number]

const snippet = (content: string) => (content.length > 120 ? `${content.slice(0, 120)}…` : content)
const pageText = (entry: CtxEntry) =>
  entry.hit.meta.page !== null ? ` · p.${entry.hit.meta.page}` : ''

/**
 * Split `answer` into plain text segments and citation markers: every "[n]" / "[n, m]" marker
 * becomes one button per number that maps to context[n]; unknown numbers stay plain text.
 */
function answerParts(
  answer: string,
  context: CtxEntry[],
  open: Set<number>,
  toggle: (n: number) => void,
): React.ReactNode[] {
  const parts: React.ReactNode[] = []
  const marker = /\[(\d+(?:\s*,\s*\d+)*)\]/g
  let last = 0
  let key = 0
  for (const match of answer.matchAll(marker)) {
    const index = match.index ?? 0
    if (index > last) parts.push(answer.slice(last, index))
    for (const raw of match[1].split(',')) {
      const n = Number(raw.trim())
      const entry = context.find((c) => c.n === n)
      if (entry !== undefined) {
        parts.push(
          <button
            key={key++}
            type="button"
            aria-pressed={open.has(n)}
            onClick={() => toggle(n)}
            className={`rounded border px-1 align-baseline text-xs ${
              open.has(n)
                ? 'border-blue-400 bg-blue-200 text-blue-900'
                : 'border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100'
            }`}
          >
            {`[${n}]`}
          </button>,
        )
      } else {
        parts.push(<span key={key++}>[{n}]</span>)
      }
    }
    last = index + match[0].length
  }
  if (last < answer.length) parts.push(answer.slice(last))
  return parts
}

/**
 * Answer text where every "[n]" / "[n, m]" marker becomes buttons "[n]" (one per number) that map to
 * context[n] (unknown n → plain text). Clicking a citation shows that chunk card (filename, page,
 * text) below and marks the button aria-pressed. streaming → blinking cursor after the text.
 * Below the answer: the context list numbered [1]..[k].
 */
export function AnswerWithCitations({
  answer,
  context,
  streaming = false,
}: AnswerWithCitationsProps): React.ReactElement {
  const [open, setOpen] = useState<Set<number>>(() => new Set())
  const toggle = (n: number) =>
    setOpen((prev) => {
      const next = new Set(prev)
      if (next.has(n)) next.delete(n)
      else next.add(n)
      return next
    })
  const openEntries = context.filter((entry) => open.has(entry.n))

  return (
    <section className="space-y-3">
      <p className="text-sm text-gray-800">
        <span>{answerParts(answer, context, open, toggle)}</span>
        {streaming ? (
          <span aria-hidden="true" className="ml-0.5 animate-pulse text-gray-400">
            ▌
          </span>
        ) : null}
      </p>
      {openEntries.length > 0 ? (
        <div className="space-y-2">
          {openEntries.map((entry) => (
            <article key={entry.n} className="rounded border border-gray-200 bg-white p-3">
              <header className="mb-1 flex items-baseline gap-2 text-sm">
                <span className="font-medium text-gray-800">{entry.hit.meta.filename}</span>
                <span className="text-xs text-gray-500">
                  {entry.hit.meta.page !== null ? `p.${entry.hit.meta.page}` : ''}
                </span>
              </header>
              <p className="whitespace-pre-line text-sm text-gray-600">{entry.hit.content}</p>
            </article>
          ))}
        </div>
      ) : null}
      <ol className="space-y-1">
        {context.map((entry) => (
          <li key={entry.n} className="flex gap-2 text-xs text-gray-500">
            <span className="shrink-0">{`[${entry.n}]`}</span>
            <span className="truncate">
              {entry.hit.meta.filename}
              {pageText(entry)} — {snippet(entry.hit.content)}
            </span>
          </li>
        ))}
      </ol>
    </section>
  )
}
