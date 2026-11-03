import { useState } from 'react'

import type { ChunkArtifact, EmbedArtifact } from '../../api/types'
import { ScatterPlot } from '../../viz/ScatterPlot'
import { SimilarityMatrix } from '../../viz/SimilarityMatrix'
import { TokenView } from '../../viz/TokenView'
import { VectorHeatmap } from '../../viz/VectorHeatmap'

export interface EmbedViewProps {
  stageRunId: string
  artifact: EmbedArtifact
  chunks?: ChunkArtifact['chunks']
}

type TabId = 'tokens' | 'heatmap' | 'projection' | 'similarity'

/**
 * Header: "<n> chunks · <dense_model> (<dims>d) · <sparse_model>" + "<k> over limit" badge. Tabs are
 * <button role="tab"> (accessible name = label) above one <div role="tabpanel">: "Tokens" (chunk
 * selector + <TokenView>), "Heatmap" (<VectorHeatmap> of sampled chunks' dense vectors, labels "#index"),
 * "Projection" (two buttons named exactly "PCA" and "UMAP", default PCA, + <ScatterPlot>; groups =
 * element_type of props.chunks when given, else 'chunk'), "Similarity" (<SimilarityMatrix> labels
 * "#index"). Notice: "Vectors are not stored yet — run Store to write them to Qdrant."
 */
export function EmbedView({ artifact, chunks }: EmbedViewProps): React.ReactElement {
  const [tab, setTab] = useState<TabId>('tokens')
  const [chunkIndex, setChunkIndex] = useState(0)
  const [method, setMethod] = useState<'pca' | 'umap'>('pca')
  const tabs: { id: TabId; label: string }[] = [
    { id: 'tokens', label: 'Tokens' },
    { id: 'heatmap', label: 'Heatmap' },
    { id: 'projection', label: 'Projection' },
    { id: 'similarity', label: 'Similarity' },
  ]
  const overLimitCount = artifact.chunks.filter((c) => c.over_limit).length
  const sampleLabels = artifact.sample_indices.map((i) => `#${i}`)
  const sampleVectors = artifact.sample_indices.map((i) => artifact.chunks[i].dense)
  const groups = sampleLabels.map(
    (_label, p) =>
      chunks?.find((c) => c.index === artifact.sample_indices[p])?.element_type ?? 'chunk',
  )
  const selected = artifact.chunks[chunkIndex]
  const points2d = method === 'pca' ? artifact.projections.pca2 : artifact.projections.umap2
  const points3d = method === 'pca' ? artifact.projections.pca3 : artifact.projections.umap3
  const methodClass = (active: boolean) =>
    `rounded border px-2 py-1 text-sm ${
      active ? 'border-gray-900 bg-gray-900 text-white' : 'border-gray-300 bg-white text-gray-700'
    }`

  return (
    <section className="flex flex-col gap-3 p-4">
      <header className="flex items-center gap-2 text-sm">
        <span>
          {`${artifact.chunks.length} chunks · ${artifact.dense_model} (${artifact.dense_dims}d) · ${artifact.sparse_model}`}
        </span>
        {overLimitCount > 0 ? (
          <span className="rounded bg-red-100 px-1.5 py-0.5 text-xs font-medium text-red-700">
            {`${overLimitCount} over limit`}
          </span>
        ) : null}
      </header>
      <p className="text-xs text-gray-500">
        Vectors are not stored yet — run Store to write them to Qdrant.
      </p>
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
        {tab === 'tokens' ? (
          <div className="flex flex-col gap-3">
            <select
              value={chunkIndex}
              onChange={(e) => setChunkIndex(Number(e.target.value))}
              className="rounded border border-gray-300 bg-white px-2 py-1 text-sm"
            >
              {artifact.chunks.map((c, i) => (
                <option key={c.index} value={i}>
                  #{c.index}
                </option>
              ))}
            </select>
            <TokenView
              tokens={selected.tokens}
              tokenCount={selected.token_count}
              maxTokens={artifact.max_tokens}
              overLimit={selected.over_limit}
            />
          </div>
        ) : tab === 'heatmap' ? (
          <VectorHeatmap vectors={sampleVectors} labels={sampleLabels} />
        ) : tab === 'projection' ? (
          <div className="flex flex-col gap-2">
            <div className="flex gap-1">
              <button
                type="button"
                className={methodClass(method === 'pca')}
                onClick={() => setMethod('pca')}
              >
                PCA
              </button>
              <button
                type="button"
                className={methodClass(method === 'umap')}
                onClick={() => setMethod('umap')}
              >
                UMAP
              </button>
            </div>
            <ScatterPlot
              points2d={points2d}
              points3d={points3d}
              labels={sampleLabels}
              groups={groups}
              method={method}
            />
          </div>
        ) : (
          <SimilarityMatrix matrix={artifact.similarity} labels={sampleLabels} />
        )}
      </div>
    </section>
  )
}
