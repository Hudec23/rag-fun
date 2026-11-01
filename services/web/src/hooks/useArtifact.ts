/** react-query ['artifact', stageRunId] via getArtifact<T>; disabled when stageRunId is null;
 * staleTime Infinity (artifacts never change). */
export function useArtifact<T>(_stageRunId: string | null): {
  data: T | undefined
  error: unknown
  isLoading: boolean
} {
  throw new Error('not implemented')
}
