import { apiFetch } from './client'
import type { FacetResponse, PayloadFilter, QdrantInfo, QdrantPoint, ScrollResponse } from './types'

export function getQdrantInfo(collectionId: string): Promise<QdrantInfo> {
  return apiFetch<QdrantInfo>(`/collections/${collectionId}/qdrant`)
}

/** POST /collections/{id}/qdrant/scroll. */
export function scrollPoints(
  collectionId: string,
  req: { filter: PayloadFilter; limit: number; offset: string | null; with_vectors: boolean },
): Promise<ScrollResponse> {
  return apiFetch<ScrollResponse>(`/collections/${collectionId}/qdrant/scroll`, {
    method: 'POST',
    body: req,
  })
}

/** POST /collections/{id}/qdrant/count → number. */
export function countPoints(collectionId: string, filter: PayloadFilter): Promise<number> {
  return apiFetch<{ count: number }>(`/collections/${collectionId}/qdrant/count`, {
    method: 'POST',
    body: { filter },
  }).then((res) => res.count)
}

export function getFacet(collectionId: string, key: string): Promise<FacetResponse> {
  return apiFetch<FacetResponse>(`/collections/${collectionId}/qdrant/facets/${key}`)
}

export function getPoint(collectionId: string, pointId: string): Promise<QdrantPoint> {
  return apiFetch<QdrantPoint>(`/collections/${collectionId}/qdrant/points/${pointId}`)
}
