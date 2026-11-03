import { useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { getIngestRun, getQueryRun } from '../api/runs'
import type { IngestRun, QueryRun, RunEvent } from '../api/types'
import { useRunEvents } from './useRunEvents'

export interface LiveRun<T> {
  run: T | undefined
  error: unknown
  /** latest stage.progress per stage_run_id */
  progress: Record<string, { done: number; total: number; message: string }>
  /** generate.token texts joined in index order per stage_run_id */
  tokens: Record<string, string>
}

/** react-query [runKey, runId] via fetchRun + useRunEvents: run.updated, stage.started,
 * stage.completed, stage.failed → invalidate the query; stage.progress → progress map;
 * generate.token → token buffer per stage_run_id, texts joined in index order. */
function useLiveRun<T>(
  runKey: readonly [string, string],
  runId: string,
  fetchRun: () => Promise<T>,
): LiveRun<T> {
  const queryClient = useQueryClient()
  const tokenBuffers = useRef<Record<string, Map<number, string>>>({})
  const [progress, setProgress] = useState<LiveRun<T>['progress']>({})
  const [tokens, setTokens] = useState<LiveRun<T>['tokens']>({})
  const { data, error } = useQuery<T>({ queryKey: runKey, queryFn: fetchRun })
  useRunEvents(runId, (e: RunEvent) => {
    switch (e.type) {
      case 'stage.started':
      case 'stage.completed':
      case 'stage.failed':
      case 'run.updated':
        void queryClient.invalidateQueries({ queryKey: runKey })
        break
      case 'stage.progress':
        setProgress((prev) => ({
          ...prev,
          [e.stage_run_id]: { done: e.done, total: e.total, message: e.message },
        }))
        break
      case 'generate.token': {
        const buffer = (tokenBuffers.current[e.stage_run_id] ??= new Map<number, string>())
        buffer.set(e.index, e.text)
        const joined = [...buffer.entries()]
          .sort((a, b) => a[0] - b[0])
          .map(([, text]) => text)
          .join('')
        setTokens((prev) => ({ ...prev, [e.stage_run_id]: joined }))
        break
      }
    }
  })
  return { run: data, error, progress, tokens }
}

/** react-query ['ingest-run', runId] via getIngestRun + useRunEvents: run.updated, stage.started,
 * stage.completed, stage.failed → invalidate the query; stage.progress → progress map. */
export function useIngestRun(runId: string): LiveRun<IngestRun> {
  return useLiveRun(['ingest-run', runId], runId, () => getIngestRun(runId))
}

/** Same for query runs (['query-run', runId], getQueryRun); generate.token → tokens map. */
export function useQueryRun(runId: string): LiveRun<QueryRun> {
  return useLiveRun(['query-run', runId], runId, () => getQueryRun(runId))
}
