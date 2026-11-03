import { apiFetch } from './client'
import type { Collection, CollectionCreate, CollectionList } from './types'

export function listCollections(): Promise<CollectionList> {
  return apiFetch<CollectionList>('/collections')
}

/** POST /collections → 201 Collection. */
export function createCollection(body: CollectionCreate): Promise<Collection> {
  return apiFetch<Collection>('/collections', { method: 'POST', body })
}

/** DELETE /collections/{id} → 204. */
export function deleteCollection(id: string): Promise<void> {
  return apiFetch<void>(`/collections/${id}`, { method: 'DELETE' })
}
