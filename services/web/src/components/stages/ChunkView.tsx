import { useState } from 'react'

import type { ChunkArtifact } from '../../api/types'
import { ChunkHighlighter } from '../../viz/ChunkHighlighter'
import { LengthHistogram } from '../../viz/LengthHistogram'

export interface ChunkViewProps {
  stageRunId: string
  artifact: ChunkArtifact
}

type TabId = 'source' | 'cards' | 'histogram' | 'breakpoints'

/**
 * Header: "<count> chunks · <min>–<max> chars · mean <mean>" + strategy name. Tabs are
 * <button role="tab"> (accessible name = label) above one <div role="tabpanel">: "Source"
 * (<ChunkHighlighter>), "Cards" (one card per chunk: #index, element_type badge, pages, section path
 * joined ' › ', text), "Histogram" (<LengthHistogram>). Semantic strategy: extra tab "Breakpoints"
 * listing gaps with distance (3 decimals) and a ✂ marker where is_break.
 */
export function ChunkView({ artifact }: ChunkViewProps): React.ReactElement {
  const { strategy, source_text, chunks, stats, semantic } = artifact
  const [tab, setTab] = useState<TabId>('source')
  const tabs: { id: TabId; label: string }[] = [
    { id: 'source', label: 'Source' },
    { id: 'cards', label: 'Cards' },
    { id: 'histogram', label: 'Histogram' },
  ]
  if (semantic !== null) tabs.push({ id: 'breakpoints', label: 'Breakpoints' })

  return (
    <section className="flex flex-col gap-3 p-4">
      <header className="flex items-center gap-2 text-sm">
        <span>
          {`${stats.count} chunks · ${stats.min_chars}–${stats.max_chars} chars · mean ${stats.mean_chars}`}
        </span>
        <span className="rounded bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-800">
          {strategy}
        </span>
      </header>
      <div role="tablist" className="flex gap-1">
        {tabs.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={`rounded-t border-b-2 px-3 py-1 text-sm ${
              tab === t.id
                ? 'border-blue-600 font-medium text-blue-700'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div role="tabpanel">
        {tab === 'source' ? (
          <ChunkHighlighter sourceText={source_text} chunks={chunks} />
        ) : tab === 'cards' ? (
          <ul className="flex flex-col gap-2">
            {chunks.map((c) => (
              <li key={c.index} className="rounded border border-gray-200 bg-white p-3 text-sm">
                <div className="mb-1 flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs font-medium text-gray-600">#{c.index}</span>
                  <span className="rounded-sm bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-800">
                    {c.element_type}
                  </span>
                  {c.page_numbers.length > 0 ? (
                    <span className="text-xs text-gray-500">pages {c.page_numbers.join(', ')}</span>
                  ) : null}
                  {c.section_path.length > 0 ? (
                    <span className="text-xs text-gray-500">{c.section_path.join(' › ')}</span>
                  ) : null}
                </div>
                <p className="whitespace-pre-wrap break-words">{c.text}</p>
              </li>
            ))}
          </ul>
        ) : tab === 'histogram' ? (
          <LengthHistogram binEdges={stats.histogram.bin_edges} counts={stats.histogram.counts} />
        ) : semantic !== null ? (
          <ul className="flex flex-col gap-1">
            {semantic.gaps.map((g, i) => (
              <li
                key={i}
                className="flex items-center gap-3 rounded border border-gray-200 bg-white px-3 py-1.5 text-sm"
              >
                <span className="text-gray-600">after sentence {g.after_sentence}</span>
                <span className="font-mono">{g.distance.toFixed(3)}</span>
                {g.is_break ? <span aria-label="breakpoint">✂</span> : null}
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </section>
  )
}
