import type { Stage, StageRun } from '../api/types'

export interface StagePanelProps {
  runId: string
  runKind: 'ingest' | 'query'
  stage: Stage
  run: StageRun | null
  progress?: { done: number; total: number; message: string }
  liveText?: string | null
  extra?: Record<string, unknown>
}

/**
 * One stage of a run: <ParamsForm> initialised from run.params (or lib/defaults), "Run <stage>" button
 * → startIngestStage / startQueryStage (ApiError → ErrorBox, e.g. STAGE_PREREQUISITE_MISSING), status
 * line, <ProgressBar> while queued/running, error box when failed (error.code: error.message), stale
 * banner "Outdated — an earlier stage was re-run", <VersionPicker>; when the selected version is done:
 * useArtifact + the stage's <XView> (props from `extra`: collectionId, chunks). Retrieve stage also
 * shows <FilterBuilder> bound to params.filters (needs extra.collectionId).
 */
export function StagePanel(_props: StagePanelProps): React.ReactElement {
  throw new Error('not implemented')
}
