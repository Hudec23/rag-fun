import { Fragment } from 'react'

import type { StoreArtifact } from '../../api/types'

export interface StoreViewProps {
  stageRunId: string
  artifact: StoreArtifact
  collectionId?: string
}

/**
 * Summary: "<points_written> points written to <qdrant_collection>" (+ "<points_deleted> old
 * points replaced" when > 0). Vector config table (dense name/size/distance, sparse name/modifier).
 * Payload sample as pretty JSON (<pre>) with filterable keys (meta.*) highlighted. Link "Open in Qdrant
 * browser" → /qdrant/<collectionId>.
 */
export function StoreView({ artifact, collectionId }: StoreViewProps): React.ReactElement {
  const { qdrant_collection, points_written, points_deleted, payload_sample, vector_config } =
    artifact

  return (
    <section className="flex flex-col gap-3 p-4">
      <header className="flex flex-wrap items-center gap-2 text-sm">
        <span>{`${points_written} points written to ${qdrant_collection}`}</span>
        {points_deleted > 0 ? (
          <span className="rounded bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-800">
            {`${points_deleted} old points replaced`}
          </span>
        ) : null}
        {collectionId ? (
          <a className="text-blue-700 underline" href={`/qdrant/${collectionId}`}>
            Open in Qdrant browser
          </a>
        ) : null}
      </header>
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-gray-200 text-left text-xs uppercase tracking-wide text-gray-500">
            <th className="py-1 pr-3 font-medium">Vector</th>
            <th className="py-1 pr-3 font-medium">Name</th>
            <th className="py-1 pr-3 font-medium">Size</th>
            <th className="py-1 pr-3 font-medium">Distance</th>
            <th className="py-1 font-medium">Modifier</th>
          </tr>
        </thead>
        <tbody>
          <tr className="border-b border-gray-100">
            <td className="py-1 pr-3 text-gray-600">dense</td>
            <td className="py-1 pr-3 font-mono">{vector_config.dense_name}</td>
            <td className="py-1 pr-3">{vector_config.dense_size}</td>
            <td className="py-1 pr-3">{vector_config.distance}</td>
            <td className="py-1 text-gray-400">—</td>
          </tr>
          <tr className="border-b border-gray-100">
            <td className="py-1 pr-3 text-gray-600">sparse</td>
            <td className="py-1 pr-3 font-mono">{vector_config.sparse_name}</td>
            <td className="py-1 pr-3 text-gray-400">—</td>
            <td className="py-1 pr-3 text-gray-400">—</td>
            <td className="py-1">{vector_config.sparse_modifier}</td>
          </tr>
        </tbody>
      </table>
      <div>
        <h3 className="mb-1 text-sm font-medium text-gray-700">Payload sample</h3>
        <pre className="overflow-x-auto rounded border border-gray-200 bg-gray-50 p-3 text-xs leading-relaxed">
          {renderJson(payload_sample, '')}
        </pre>
      </div>
    </section>
  )
}

/** True for the Qdrant-filterable payload keys: the `meta` object and everything inside it. */
function isFilterable(path: string): boolean {
  return path === 'meta' || path.startsWith('meta.')
}

function keySpan(key: string, path: string): React.ReactElement {
  return (
    <span
      className={
        isFilterable(path) ? 'rounded-sm bg-amber-200 font-medium text-amber-900' : 'text-sky-700'
      }
    >
      {JSON.stringify(key)}
    </span>
  )
}

/** Pretty-print a JSON value (2-space indent, like `JSON.stringify(v, null, 2)`) with keys as
 * spans; filterable keys (meta.*) get a highlight. */
function renderJson(value: unknown, path: string, indent: number = 0): React.ReactNode {
  if (value === null || typeof value === 'number' || typeof value === 'boolean') {
    return String(value)
  }
  if (typeof value === 'string') {
    return JSON.stringify(value)
  }
  if (Array.isArray(value)) {
    if (value.length === 0) return '[]'
    const inner = '  '.repeat(indent + 1)
    return (
      <>
        {'[\n'}
        {value.map((item, i) => (
          <Fragment key={i}>
            {inner}
            {renderJson(item, `${path}[${i}]`, indent + 1)}
            {i < value.length - 1 ? ',\n' : ''}
          </Fragment>
        ))}
        {`\n${'  '.repeat(indent)}]`}
      </>
    )
  }
  const entries = Object.entries(value as Record<string, unknown>)
  if (entries.length === 0) return '{}'
  const inner = '  '.repeat(indent + 1)
  return (
    <>
      {'{\n'}
      {entries.map(([key, item], i) => (
        <Fragment key={key}>
          {inner}
          {keySpan(key, `${path}.${key}`)}
          {': '}
          {renderJson(item, `${path}.${key}`, indent + 1)}
          {i < entries.length - 1 ? ',\n' : ''}
        </Fragment>
      ))}
      {`\n${'  '.repeat(indent)}}`}
    </>
  )
}
