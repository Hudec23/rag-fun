import { apiFetch } from './client'
import type { Collection, CollectionCreate, CollectionList } from './types'

export function listCollections(): Promise<CollectionList> {
  return apiFetch<CollectionList>('/collections')
}

/** POST /collections → 201 Collection. */
export function createCollection(_body: CollectionCreate): Promise<Collection> {
  throw new Error('not implemented')
}

/** DELETE /collections/{id} → 204. */
export function deleteCollection(_id: string): Promise<void> {
  throw new Error('not implemented')
}
