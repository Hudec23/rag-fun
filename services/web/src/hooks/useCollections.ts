import { useQuery } from '@tanstack/react-query'

import { listCollections } from '../api/collections'

export const collectionsKey = ['collections'] as const

export function useCollections() {
  return useQuery({ queryKey: collectionsKey, queryFn: listCollections })
}
