import type { IngestRun, QueryRun } from '../api/types'

export interface LiveRun<T> {
  run: T | undefined
  error: unknown
  /** latest stage.progress per stage_run_id */
  progress: Record<string, { done: number; total: number; message: string }>
  /** generate.token texts joined in index order per stage_run_id */
  tokens: Record<string, string>
}

/** react-query ['ingest-run', runId] via getIngestRun + useRunEvents: run.updated, stage.started,
 * stage.completed, stage.failed → invalidate the query; stage.progress → progress map. */
export function useIngestRun(_runId: string): LiveRun<IngestRun> {
  throw new Error('not implemented')
}

/** Same for query runs (['query-run', runId], getQueryRun); generate.token → tokens map. */
export function useQueryRun(_runId: string): LiveRun<QueryRun> {
  throw new Error('not implemented')
}
