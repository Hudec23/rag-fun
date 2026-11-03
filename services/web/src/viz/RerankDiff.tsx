import type { RerankArtifact } from '../api/types'

export interface RerankDiffProps {
  artifact: RerankArtifact
}

type AfterRow = RerankArtifact['after'][number]

const scoreText = (score: number) => score.toFixed(4)
const snippet = (content: string) => (content.length > 120 ? `${content.slice(0, 120)}…` : content)

const rowClass = 'flex items-baseline gap-2 px-2 py-1 text-sm'
const rankClass = 'w-4 shrink-0 text-right text-gray-400'
const scoreClass = 'w-14 shrink-0 text-gray-500'
const snippetClass = 'min-w-0 flex-1 truncate text-gray-700'

function deltaBadge(previousRank: number, newRank: number): { text: string; className: string } {
  const delta = previousRank - newRank
  if (delta > 0) return { text: `↑${delta}`, className: 'font-semibold text-green-600' }
  if (delta < 0) return { text: `↓${Math.abs(delta)}`, className: 'font-semibold text-red-600' }
  return { text: '=', className: 'font-semibold text-gray-500' }
}

function Column({
  title,
  rows,
}: {
  title: string
  rows: React.ReactElement[]
}): React.ReactElement {
  return (
    <section className="min-w-0 flex-1 rounded border border-gray-200 bg-white">
      <h3 className="border-b border-gray-200 px-2 py-1 text-sm font-semibold text-gray-700">
        {title}
      </h3>
      <ul className="divide-y divide-gray-100">{rows}</ul>
    </section>
  )
}

/**
 * Two columns "Before" (artifact.before) and "After" (artifact.after[].hit). After rows show
 * "↑3" (green) / "↓2" (red) / "=" from previous_rank − new rank, plus rerank_score (4 decimals) or "—".
 * disabled → banner "Reranking disabled — showing retrieval order".
 */
export function RerankDiff({ artifact }: RerankDiffProps): React.ReactElement {
  const beforeRows = artifact.before.map((hit, index) => (
    <li key={`${hit.doc_id}:${index}`} className={rowClass}>
      <span className={rankClass}>{hit.rank}</span>
      <span className={scoreClass}>{scoreText(hit.score)}</span>
      <span className={snippetClass} title={hit.content}>
        {snippet(hit.content)}
      </span>
    </li>
  ))

  const afterRows = artifact.after.map((row: AfterRow, index) => {
    const badge = deltaBadge(row.previous_rank, row.hit.rank)
    return (
      <li key={`${row.hit.doc_id}:${index}`} className={rowClass}>
        <span className={rankClass}>{row.hit.rank}</span>
        <span className={`w-7 shrink-0 ${badge.className}`}>{badge.text}</span>
        <span className={scoreClass}>
          {row.rerank_score === null ? '—' : scoreText(row.rerank_score)}
        </span>
        <span className={snippetClass} title={row.hit.content}>
          {snippet(row.hit.content)}
        </span>
      </li>
    )
  })

  return (
    <section className="space-y-3">
      {!artifact.enabled ? (
        <p className="rounded border border-amber-200 bg-amber-50 px-2 py-1 text-sm text-amber-800">
          Reranking disabled — showing retrieval order
        </p>
      ) : null}
      <div className="flex flex-col gap-4 xl:flex-row">
        <Column title="Before" rows={beforeRows} />
        <Column title="After" rows={afterRows} />
      </div>
    </section>
  )
}
