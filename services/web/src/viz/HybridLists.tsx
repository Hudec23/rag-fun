import { useState } from 'react'

import type { Hit, RetrieveArtifact } from '../api/types'

export interface HybridListsProps {
  artifact: RetrieveArtifact
}

type FusedRow = RetrieveArtifact['fused'][number]
type RowData = { hit: Hit; sources: string | null }

const scoreText = (score: number) => score.toFixed(4)
const snippet = (content: string) => (content.length > 120 ? `${content.slice(0, 120)}…` : content)
const sourceTags = (row: FusedRow) =>
  row.source_ranks.map((sr) => `${sr.list === 'dense' ? 'D' : 'S'}#${sr.rank}`).join(' ')

interface RowProps {
  row: RowData
  activeDoc: string | null
  onHover: (docId: string) => void
  onLeave: () => void
  onSelect: (docId: string) => void
}

function Row({ row, activeDoc, onHover, onLeave, onSelect }: RowProps): React.ReactElement {
  const { hit, sources } = row
  return (
    <li
      className="flex cursor-pointer items-baseline gap-2 px-2 py-1 text-sm hover:bg-gray-50"
      data-highlighted={hit.doc_id === activeDoc}
      onMouseEnter={() => onHover(hit.doc_id)}
      onMouseLeave={onLeave}
      onClick={() => onSelect(hit.doc_id)}
    >
      <span className="w-4 shrink-0 text-right text-gray-400">{hit.rank}</span>
      <span className="w-14 shrink-0 text-gray-500">{scoreText(hit.score)}</span>
      {sources !== null ? <span className="shrink-0 text-xs text-gray-500">{sources}</span> : null}
      <span className="min-w-0 flex-1 truncate text-gray-700" title={hit.content}>
        {snippet(hit.content)}
      </span>
      <span className="shrink-0 text-xs text-gray-400">
        {`${hit.meta.filename}${hit.meta.page !== null ? ` · p.${hit.meta.page}` : ''}`}
      </span>
    </li>
  )
}

interface ColumnProps {
  title: string
  rows: RowData[]
  activeDoc: string | null
  onHover: (docId: string) => void
  onLeave: () => void
  onSelect: (docId: string) => void
}

function Column({
  title,
  rows,
  activeDoc,
  onHover,
  onLeave,
  onSelect,
}: ColumnProps): React.ReactElement {
  return (
    <section className="min-w-0 flex-1 rounded border border-gray-200 bg-white">
      <h3 className="border-b border-gray-200 px-2 py-1 text-sm font-semibold text-gray-700">
        {title}
      </h3>
      <ul className="divide-y divide-gray-100">
        {rows.map((row, index) => (
          <Row
            key={`${row.hit.doc_id}:${index}`}
            row={row}
            activeDoc={activeDoc}
            onHover={onHover}
            onLeave={onLeave}
            onSelect={onSelect}
          />
        ))}
      </ul>
    </section>
  )
}

/**
 * Three columns for per_query[0] (with a query selector when per_query.length > 1): "Dense", "Sparse"
 * (column omitted when the list is null), "Fused (RRF)" from artifact.fused. Each row: rank, score (4
 * decimals), first 120 chars, filename + page. Hovering/clicking a row highlights the same doc_id in all
 * columns (data-highlighted="true"). Fused rows show source ranks as "D#2 S#5".
 */
export function HybridLists({ artifact }: HybridListsProps): React.ReactElement {
  const [queryIndex, setQueryIndex] = useState(0)
  const [hoveredDoc, setHoveredDoc] = useState<string | null>(null)
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null)
  const activeDoc = hoveredDoc ?? selectedDoc

  const perQuery = artifact.per_query
  const entry = perQuery[Math.min(queryIndex, perQuery.length - 1)] ?? null
  const dense = entry?.dense ?? null
  const sparse = entry?.sparse ?? null

  return (
    <section className="space-y-3">
      {perQuery.length > 1 ? (
        <label className="inline-flex items-center gap-2 text-sm text-gray-700">
          Query
          <select
            className="rounded border border-gray-300 bg-white px-2 py-1 text-sm"
            value={Math.min(queryIndex, perQuery.length - 1)}
            onChange={(event) => setQueryIndex(Number(event.target.value))}
          >
            {perQuery.map((query, index) => (
              <option key={index} value={index}>
                {query.query}
              </option>
            ))}
          </select>
        </label>
      ) : null}
      <div className="flex flex-col gap-4 xl:flex-row">
        {dense !== null ? (
          <Column
            title="Dense"
            rows={dense.map((hit) => ({ hit, sources: null }))}
            activeDoc={activeDoc}
            onHover={setHoveredDoc}
            onLeave={() => setHoveredDoc(null)}
            onSelect={setSelectedDoc}
          />
        ) : null}
        {sparse !== null ? (
          <Column
            title="Sparse"
            rows={sparse.map((hit) => ({ hit, sources: null }))}
            activeDoc={activeDoc}
            onHover={setHoveredDoc}
            onLeave={() => setHoveredDoc(null)}
            onSelect={setSelectedDoc}
          />
        ) : null}
        <Column
          title="Fused (RRF)"
          rows={artifact.fused.map((fused) => ({ hit: fused.hit, sources: sourceTags(fused) }))}
          activeDoc={activeDoc}
          onHover={setHoveredDoc}
          onLeave={() => setHoveredDoc(null)}
          onSelect={setSelectedDoc}
        />
      </div>
    </section>
  )
}
