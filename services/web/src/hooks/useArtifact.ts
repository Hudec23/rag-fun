import { useQuery } from '@tanstack/react-query'

import { getArtifact } from '../api/runs'

/** react-query ['artifact', stageRunId] via getArtifact<T>; disabled when stageRunId is null;
 * staleTime Infinity (artifacts never change). */
export function useArtifact<T>(stageRunId: string | null): {
  data: T | undefined
  error: unknown
  isLoading: boolean
} {
  return useQuery<T>({
    queryKey: ['artifact', stageRunId],
    queryFn: () => getArtifact<T>(stageRunId!),
    enabled: stageRunId !== null,
    staleTime: Infinity,
  })
}
