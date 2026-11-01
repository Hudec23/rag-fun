import type {
  IngestParamsAll,
  IngestRun,
  IngestStage,
  QueryRun,
  QueryStage,
  Stage,
  StageRun,
  StageRunList,
} from './types'
import { API_BASE } from './client'

/** POST /ingest-runs → 201 IngestRun. */
export function createIngestRun(_fileId: string, _collectionId: string): Promise<IngestRun> {
  throw new Error('not implemented')
}

export function getIngestRun(_runId: string): Promise<IngestRun> {
  throw new Error('not implemented')
}

/** POST /ingest-runs/{runId}/stages/{stage} { params } → 202 StageRun. */
export function startIngestStage(
  _runId: string,
  _stage: IngestStage,
  _params: object,
): Promise<StageRun> {
  throw new Error('not implemented')
}

/** POST /ingest-runs/{runId}/run-all { from_stage, params } → IngestRun (200 or 202). */
export function runAllIngest(
  _runId: string,
  _fromStage: IngestStage | null,
  _params: IngestParamsAll,
): Promise<IngestRun> {
  throw new Error('not implemented')
}

/** POST /query-runs → 201 QueryRun. */
export function createQueryRun(_collectionId: string, _question: string): Promise<QueryRun> {
  throw new Error('not implemented')
}

export function getQueryRun(_runId: string): Promise<QueryRun> {
  throw new Error('not implemented')
}

/** POST /query-runs/{runId}/stages/{stage} { params } → 202 StageRun. */
export function startQueryStage(
  _runId: string,
  _stage: QueryStage,
  _params: object,
): Promise<StageRun> {
  throw new Error('not implemented')
}

/** GET /stage-runs?run_id=&stage= (all versions, newest first). */
export function listStageRuns(_runId: string, _stage: Stage): Promise<StageRunList> {
  throw new Error('not implemented')
}

/** GET /stage-runs/{id}/artifact. */
export function getArtifact<T>(_stageRunId: string): Promise<T> {
  throw new Error('not implemented')
}

export function pageImageUrl(stageRunId: string, pageNo: number): string {
  return `${API_BASE}/stage-runs/${stageRunId}/pages/${pageNo}`
}
