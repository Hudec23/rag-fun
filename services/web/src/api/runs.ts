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
import { API_BASE, apiFetch } from './client'

/** POST /ingest-runs → 201 IngestRun. */
export function createIngestRun(fileId: string, collectionId: string): Promise<IngestRun> {
  return apiFetch<IngestRun>('/ingest-runs', {
    method: 'POST',
    body: { file_id: fileId, collection_id: collectionId },
  })
}

export function getIngestRun(runId: string): Promise<IngestRun> {
  return apiFetch<IngestRun>(`/ingest-runs/${runId}`)
}

/** POST /ingest-runs/{runId}/stages/{stage} { params } → 202 StageRun. */
export function startIngestStage(
  runId: string,
  stage: IngestStage,
  params: object,
): Promise<StageRun> {
  return apiFetch<StageRun>(`/ingest-runs/${runId}/stages/${stage}`, {
    method: 'POST',
    body: { params },
  })
}

/** POST /ingest-runs/{runId}/run-all { from_stage, params } → IngestRun (200 or 202). */
export function runAllIngest(
  runId: string,
  fromStage: IngestStage | null,
  params: IngestParamsAll,
): Promise<IngestRun> {
  return apiFetch<IngestRun>(`/ingest-runs/${runId}/run-all`, {
    method: 'POST',
    body: { from_stage: fromStage, params },
  })
}

/** POST /query-runs → 201 QueryRun. */
export function createQueryRun(collectionId: string, question: string): Promise<QueryRun> {
  return apiFetch<QueryRun>('/query-runs', {
    method: 'POST',
    body: { collection_id: collectionId, question },
  })
}

export function getQueryRun(runId: string): Promise<QueryRun> {
  return apiFetch<QueryRun>(`/query-runs/${runId}`)
}

/** POST /query-runs/{runId}/stages/{stage} { params } → 202 StageRun. */
export function startQueryStage(
  runId: string,
  stage: QueryStage,
  params: object,
): Promise<StageRun> {
  return apiFetch<StageRun>(`/query-runs/${runId}/stages/${stage}`, {
    method: 'POST',
    body: { params },
  })
}

/** POST /query-runs/{runId}/run-all { from_stage, params } → QueryRun (200 or 202). */
export function runAllQuery(
  runId: string,
  fromStage: QueryStage | null,
  params: { transform: object; retrieve: object; rerank: object; generate: object },
): Promise<QueryRun> {
  return apiFetch<QueryRun>(`/query-runs/${runId}/run-all`, {
    method: 'POST',
    body: { from_stage: fromStage, params },
  })
}

/** GET /stage-runs?run_id=&stage= (all versions, newest first). */
export function listStageRuns(runId: string, stage: Stage): Promise<StageRunList> {
  return apiFetch<StageRunList>(`/stage-runs?run_id=${encodeURIComponent(runId)}&stage=${stage}`)
}

/** GET /stage-runs/{id}/artifact. */
export function getArtifact<T>(stageRunId: string): Promise<T> {
  return apiFetch<T>(`/stage-runs/${stageRunId}/artifact`)
}

export function pageImageUrl(stageRunId: string, pageNo: number): string {
  return `${API_BASE}/stage-runs/${stageRunId}/pages/${pageNo}`
}
