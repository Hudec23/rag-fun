import type { FacetResponse, PayloadFilter, QdrantInfo, QdrantPoint, ScrollResponse } from './types'

export function getQdrantInfo(_collectionId: string): Promise<QdrantInfo> {
  throw new Error('not implemented')
}

/** POST /collections/{id}/qdrant/scroll. */
export function scrollPoints(
  _collectionId: string,
  _req: { filter: PayloadFilter; limit: number; offset: string | null; with_vectors: boolean },
): Promise<ScrollResponse> {
  throw new Error('not implemented')
}

/** POST /collections/{id}/qdrant/count → number. */
export function countPoints(_collectionId: string, _filter: PayloadFilter): Promise<number> {
  throw new Error('not implemented')
}

export function getFacet(_collectionId: string, _key: string): Promise<FacetResponse> {
  throw new Error('not implemented')
}

export function getPoint(_collectionId: string, _pointId: string): Promise<QdrantPoint> {
  throw new Error('not implemented')
}
