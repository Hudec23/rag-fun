/**
 * Route "/pipelines". listPipelineGraphs → left list with one "stage / variant" entry per reported
 * graph; the selected graph (first by default) rendered with <PipelineGraph>. Empty → "No pipeline
 * graphs reported yet — is the worker running?"
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { listPipelineGraphs } from '../api/system'
import { ErrorBox } from '../components/ErrorBox'
import { PipelineGraph } from '../viz/PipelineGraph'

const LIST_BUTTON_CLASS = 'block w-full rounded px-2 py-1 text-left text-sm hover:bg-gray-50'

/** Key of a graph entry, e.g. "chunk/fixed". */
function keyOf(graph: { stage: string; variant: string }): string {
  return `${graph.stage}/${graph.variant}`
}

export function PipelinesPage(): React.ReactElement {
  const graphs = useQuery({
    queryKey: ['pipeline-graphs'],
    queryFn: listPipelineGraphs,
  })
  const [selected, setSelected] = useState<string | null>(null)
  const items = graphs.data ?? []
  const active = items.find((graph) => keyOf(graph) === selected) ?? items[0] ?? null
  const activeKey = active !== null ? keyOf(active) : null

  return (
    <section className="space-y-4 p-4">
      <h1 className="text-lg font-semibold">Pipelines</h1>
      {graphs.isLoading ? (
        <p className="text-sm text-gray-500">Loading…</p>
      ) : graphs.error ? (
        <ErrorBox error={graphs.error} />
      ) : items.length === 0 ? (
        <p className="text-sm text-gray-500">
          No pipeline graphs reported yet — is the worker running?
        </p>
      ) : (
        <div className="flex flex-col gap-4 xl:flex-row">
          <ul className="w-full divide-y rounded border bg-white xl:w-48">
            {items.map((graph) => (
              <li key={keyOf(graph)}>
                <button
                  type="button"
                  onClick={() => setSelected(keyOf(graph))}
                  className={
                    keyOf(graph) === activeKey
                      ? `${LIST_BUTTON_CLASS} bg-gray-100 font-medium`
                      : LIST_BUTTON_CLASS
                  }
                >
                  {graph.stage} / {graph.variant}
                </button>
              </li>
            ))}
          </ul>
          {active !== null ? <PipelineGraph key={activeKey} graph={active} /> : null}
        </div>
      )}
    </section>
  )
}
