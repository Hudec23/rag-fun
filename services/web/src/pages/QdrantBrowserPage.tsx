/**
 * Route "/qdrant/:collectionId?". Collection select (navigates). Info card from getQdrantInfo: exists,
 * status, points_count, vector config (shows the names text-dense / text-sparse, size, distance,
 * modifier), payload indexes table. <FilterBuilder> + matching count (countPoints). Points table
 * (scrollPoints limit 20, "Load more" with next_offset): point id (first 8), filename, page,
 * element_type, tags, content (80 chars). Click row → side panel with getPoint raw JSON (<pre>) showing
 * the first 16 dense dims + "… (<n> more)". exists false → "Nothing stored yet in this collection — run
 * the Store stage of an ingest run."
 */
import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router'

import { countPoints, getPoint, getQdrantInfo, scrollPoints } from '../api/qdrant'
import type { PayloadFilter, QdrantInfo, QdrantPoint } from '../api/types'
import { ErrorBox } from '../components/ErrorBox'
import { FilterBuilder } from '../components/FilterBuilder'
import { useCollections } from '../hooks/useCollections'

const PAGE_SIZE = 20
const DENSE_PREVIEW = 16
const CONTROL_CLASS = 'rounded border border-gray-300 bg-white px-2 py-1 text-sm'

/** Content cell: max 80 chars, "…" when cut. */
function truncateContent(content: string): string {
  return content.length > 80 ? `${content.slice(0, 80)}…` : content
}

/** Panel JSON: id, payload, vectors with only the first DENSE_PREVIEW dense dims. */
function panelJson(point: QdrantPoint): string {
  return JSON.stringify(
    {
      id: point.id,
      payload: point.payload,
      vectors: point.vectors
        ? {
            dense: point.vectors.dense.slice(0, DENSE_PREVIEW),
            sparse: point.vectors.sparse,
          }
        : null,
    },
    null,
    2,
  )
}

function InfoCard({ info }: { info: QdrantInfo }): React.ReactElement {
  return (
    <section className="space-y-3 rounded border bg-white p-4">
      <div className="flex flex-wrap items-center gap-3 text-sm text-gray-700">
        <span>
          Status: <span>{info.status}</span>
        </span>
        <span>{info.points_count ?? 0} points</span>
      </div>
      {info.dense !== null || info.sparse !== null ? (
        <ul className="space-y-1 text-sm text-gray-700">
          {info.dense !== null ? (
            <li>
              <span>{info.dense.name}</span>
              {' · '}
              {info.dense.size}d · {info.dense.distance}
            </li>
          ) : null}
          {info.sparse !== null ? (
            <li>
              <span>{info.sparse.name}</span>
              {' · '}
              {info.sparse.modifier}
            </li>
          ) : null}
        </ul>
      ) : null}
      {info.payload_indexes.length > 0 ? (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-left text-xs uppercase text-gray-500">
              <th className="p-2 font-medium">Payload index</th>
              <th className="p-2 font-medium">Type</th>
              <th className="p-2 font-medium">Points</th>
            </tr>
          </thead>
          <tbody>
            {info.payload_indexes.map((idx) => (
              <tr key={idx.key} className="border-b border-gray-100">
                <td className="p-2">{idx.key}</td>
                <td className="p-2">{idx.type}</td>
                <td className="p-2">{idx.points}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </section>
  )
}

function PointPanel({
  collectionId,
  pointId,
  onClose,
}: {
  collectionId: string
  pointId: string
  onClose: () => void
}): React.ReactElement {
  const point = useQuery({
    queryKey: ['qdrant', 'point', collectionId, pointId],
    queryFn: () => getPoint(collectionId, pointId),
  })
  return (
    <aside className="space-y-3 rounded border bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-mono text-sm font-semibold">{pointId}</h2>
        <button type="button" onClick={onClose} className={CONTROL_CLASS}>
          Close
        </button>
      </div>
      {point.isLoading ? (
        <p className="text-sm text-gray-500">Loading…</p>
      ) : point.error ? (
        <ErrorBox error={point.error} />
      ) : point.data ? (
        <>
          <pre className="overflow-x-auto rounded border border-gray-200 p-2 text-xs">
            {panelJson(point.data)}
          </pre>
          {point.data.vectors && point.data.vectors.dense.length > DENSE_PREVIEW ? (
            <p className="text-xs text-gray-500">
              … ({point.data.vectors.dense.length - DENSE_PREVIEW} more)
            </p>
          ) : null}
        </>
      ) : null}
    </aside>
  )
}

export function QdrantBrowserPage(): React.ReactElement {
  const navigate = useNavigate()
  const { collectionId } = useParams()
  const routeId = collectionId ?? ''
  const collections = useCollections()
  const [filter, setFilter] = useState<PayloadFilter>({ must: [] })
  const [lastRouteId, setLastRouteId] = useState(routeId)
  const [lastFilter, setLastFilter] = useState<PayloadFilter>(filter)
  const [points, setPoints] = useState<QdrantPoint[]>([])
  const [nextOffset, setNextOffset] = useState<string | null>(null)
  const [pointsLoading, setPointsLoading] = useState(true)
  const [pointsError, setPointsError] = useState<unknown>(null)
  const [loadingMore, setLoadingMore] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const info = useQuery({
    queryKey: ['qdrant', 'info', routeId],
    queryFn: () => getQdrantInfo(routeId),
    enabled: routeId !== '',
  })
  const count = useQuery({
    queryKey: ['qdrant', 'count', routeId, JSON.stringify(filter)],
    queryFn: () => countPoints(routeId, filter),
    enabled: routeId !== '',
  })

  if (routeId !== lastRouteId || filter !== lastFilter) {
    setLastRouteId(routeId)
    setLastFilter(filter)
    setNextOffset(null)
    setPointsError(null)
    setPointsLoading(true)
    if (routeId !== lastRouteId) {
      setPoints([])
      setSelectedId(null)
    }
  }

  useEffect(() => {
    if (routeId === '') return
    let cancelled = false
    scrollPoints(routeId, { filter, limit: PAGE_SIZE, offset: null, with_vectors: false })
      .then((res) => {
        if (cancelled) return
        setPoints(res.points)
        setNextOffset(res.next_offset)
      })
      .catch((err) => {
        if (cancelled) return
        setPoints([])
        setPointsError(err)
      })
      .finally(() => {
        if (!cancelled) setPointsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [routeId, filter])

  const loadMore = async () => {
    if (routeId === '' || nextOffset === null || loadingMore) return
    setLoadingMore(true)
    try {
      const res = await scrollPoints(routeId, {
        filter,
        limit: PAGE_SIZE,
        offset: nextOffset,
        with_vectors: false,
      })
      setPoints((prev) => [...prev, ...res.points])
      setNextOffset(res.next_offset)
    } catch (err) {
      setPointsError(err)
    } finally {
      setLoadingMore(false)
    }
  }

  return (
    <section className="space-y-4 p-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-lg font-semibold">Qdrant</h1>
        <select
          aria-label="Collection"
          value={routeId}
          onChange={(event) => {
            if (event.target.value !== '') navigate(`/qdrant/${event.target.value}`)
          }}
          className={CONTROL_CLASS}
        >
          <option value="">Collection…</option>
          {(collections.data?.items ?? []).map((collection) => (
            <option key={collection.id} value={collection.id}>
              {collection.name}
            </option>
          ))}
        </select>
      </div>
      {routeId === '' ? (
        <p className="text-sm text-gray-500">Select a collection to browse its stored points.</p>
      ) : !info.data || !info.data.exists ? (
        <>
          {info.isLoading ? <p className="text-sm text-gray-500">Loading…</p> : null}
          {info.error ? <ErrorBox error={info.error} /> : null}
          <p className="text-sm text-gray-500">
            Nothing stored yet in this collection — run the Store stage of an ingest run.
          </p>
        </>
      ) : (
        <>
          <InfoCard info={info.data} />
          <div className="space-y-2">
            <FilterBuilder collectionId={routeId} value={filter} onChange={setFilter} />
            {count.data !== undefined ? (
              <p className="text-sm text-gray-500">{count.data} matching</p>
            ) : null}
            {count.error ? <ErrorBox error={count.error} /> : null}
          </div>
          {pointsLoading && points.length === 0 ? (
            <p className="text-sm text-gray-500">Loading points…</p>
          ) : pointsError ? (
            <ErrorBox error={pointsError} />
          ) : points.length === 0 ? (
            <p className="text-sm text-gray-500">No points.</p>
          ) : (
            <>
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-xs uppercase text-gray-500">
                    <th className="p-2 font-medium">ID</th>
                    <th className="p-2 font-medium">Filename</th>
                    <th className="p-2 font-medium">Page</th>
                    <th className="p-2 font-medium">Type</th>
                    <th className="p-2 font-medium">Tags</th>
                    <th className="p-2 font-medium">Content</th>
                  </tr>
                </thead>
                <tbody>
                  {points.map((point) => (
                    <tr
                      key={point.id}
                      className="cursor-pointer border-b border-gray-100 align-top"
                      onClick={() => setSelectedId(point.id)}
                    >
                      <td className="p-2 font-mono">{point.id.slice(0, 8)}</td>
                      <td className="p-2">{point.payload.meta.filename}</td>
                      <td className="p-2">{point.payload.meta.page ?? '—'}</td>
                      <td className="p-2">{point.payload.meta.element_type}</td>
                      <td className="p-2">{point.payload.meta.tags.join(', ')}</td>
                      <td className="p-2">{truncateContent(point.payload.content)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {nextOffset !== null ? (
                <button
                  type="button"
                  disabled={loadingMore}
                  onClick={() => void loadMore()}
                  className={CONTROL_CLASS}
                >
                  Load more
                </button>
              ) : null}
            </>
          )}
          {selectedId !== null ? (
            <PointPanel
              collectionId={routeId}
              pointId={selectedId}
              onClose={() => setSelectedId(null)}
            />
          ) : null}
        </>
      )}
    </section>
  )
}
