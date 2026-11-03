import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { ApiError } from '../api/client'
import { listStageRuns, startIngestStage, startQueryStage } from '../api/runs'
import type {
  ChunkArtifact,
  EmbedArtifact,
  GenerateArtifact,
  IngestStage,
  ParseArtifact,
  PayloadFilter,
  QueryStage,
  RerankArtifact,
  RetrieveArtifact,
  Stage,
  StageRun,
  StoreArtifact,
  TransformArtifact,
} from '../api/types'
import { ErrorBox } from './ErrorBox'
import { FilterBuilder } from './FilterBuilder'
import { ParamsForm } from './ParamsForm'
import { ProgressBar } from './ProgressBar'
import { VersionPicker } from './VersionPicker'
import { useArtifact } from '../hooks/useArtifact'
import {
  CHUNK_DEFAULTS,
  EMBED_DEFAULTS,
  GENERATE_DEFAULTS,
  PARSE_DEFAULTS,
  RERANK_DEFAULTS,
  RETRIEVE_DEFAULTS,
  TRANSFORM_DEFAULTS,
} from '../lib/defaults'
import { ChunkView } from './stages/ChunkView'
import { EmbedView } from './stages/EmbedView'
import { GenerateView } from './stages/GenerateView'
import { ParseView } from './stages/ParseView'
import { RerankView } from './stages/RerankView'
import { RetrieveView } from './stages/RetrieveView'
import { StoreView } from './stages/StoreView'
import { TransformView } from './stages/TransformView'

export interface StagePanelProps {
  runId: string
  runKind: 'ingest' | 'query'
  stage: Stage
  run: StageRun | null
  progress?: { done: number; total: number; message: string }
  liveText?: string | null
  extra?: Record<string, unknown>
}

function seedParams(stage: Stage, run: StageRun | null): Record<string, unknown> {
  const params = run?.params
  if (params && Object.keys(params).length > 0) return { ...params }
  switch (stage) {
    case 'parse':
      return { ...PARSE_DEFAULTS.docling_layout }
    case 'chunk':
      return { ...CHUNK_DEFAULTS.recursive }
    case 'embed':
      return { ...EMBED_DEFAULTS }
    case 'store':
      return {}
    case 'transform':
      return { ...TRANSFORM_DEFAULTS }
    case 'retrieve':
      return { ...RETRIEVE_DEFAULTS }
    case 'rerank':
      return { ...RERANK_DEFAULTS }
    case 'generate':
      return { ...GENERATE_DEFAULTS }
  }
}

function StageView({
  stage,
  stageRunId,
  artifact,
  chunks,
  collectionId,
  liveText,
}: {
  stage: Stage
  stageRunId: string
  artifact: unknown
  chunks?: ChunkArtifact['chunks']
  collectionId?: string
  liveText?: string | null
}): React.ReactElement {
  switch (stage) {
    case 'parse':
      return <ParseView stageRunId={stageRunId} artifact={artifact as ParseArtifact} />
    case 'chunk':
      return <ChunkView stageRunId={stageRunId} artifact={artifact as ChunkArtifact} />
    case 'embed':
      return (
        <EmbedView stageRunId={stageRunId} artifact={artifact as EmbedArtifact} chunks={chunks} />
      )
    case 'store':
      return (
        <StoreView
          stageRunId={stageRunId}
          artifact={artifact as StoreArtifact}
          collectionId={collectionId}
        />
      )
    case 'transform':
      return <TransformView stageRunId={stageRunId} artifact={artifact as TransformArtifact} />
    case 'retrieve':
      return <RetrieveView stageRunId={stageRunId} artifact={artifact as RetrieveArtifact} />
    case 'rerank':
      return <RerankView stageRunId={stageRunId} artifact={artifact as RerankArtifact} />
    case 'generate':
      return (
        <GenerateView
          stageRunId={stageRunId}
          artifact={artifact as GenerateArtifact}
          liveText={liveText ?? null}
        />
      )
  }
}

/**
 * One stage of a run: <ParamsForm> initialised from run.params (or lib/defaults), "Run <stage>" button
 * → startIngestStage / startQueryStage (ApiError → ErrorBox, e.g. STAGE_PREREQUISITE_MISSING), status
 * line, <ProgressBar> while queued/running, error box when failed (error.code: error.message), stale
 * banner "Outdated — an earlier stage was re-run", <VersionPicker>; when the selected version is done:
 * useArtifact + the stage's <XView> (props from `extra`: collectionId, chunks). Retrieve stage also
 * shows <FilterBuilder> bound to params.filters (needs extra.collectionId).
 */
export function StagePanel({
  runId,
  runKind,
  stage,
  run,
  progress,
  liveText,
  extra,
}: StagePanelProps): React.ReactElement {
  const [params, setParams] = useState<Record<string, unknown>>(() => seedParams(stage, run))
  const [selectedId, setSelectedId] = useState<string | null>(() => run?.id ?? null)
  const [error, setError] = useState<unknown>(null)
  const [starting, setStarting] = useState(false)

  // Same query key as <VersionPicker>: the list is fetched once and shared.
  const { data: list } = useQuery({
    queryKey: ['stage-runs', runId, stage],
    queryFn: () => listStageRuns(runId, stage),
  })
  const selectedRun =
    list?.items.find((item) => item.id === selectedId) ??
    (run && run.id === selectedId ? run : null)
  const viewId = selectedRun?.status === 'done' ? selectedRun.id : null
  const { data: artifact } = useArtifact<unknown>(viewId)

  const collectionId = typeof extra?.collectionId === 'string' ? extra.collectionId : undefined
  const chunks = extra?.chunks as ChunkArtifact['chunks'] | undefined

  const start = async () => {
    setError(null)
    setStarting(true)
    try {
      if (runKind === 'ingest') {
        await startIngestStage(runId, stage as IngestStage, params)
      } else {
        await startQueryStage(runId, stage as QueryStage, params)
      }
    } catch (err) {
      setError(err)
    } finally {
      setStarting(false)
    }
  }

  return (
    <section className="space-y-3 p-4">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-base font-semibold">{stage}</h2>
        <VersionPicker
          runId={runId}
          stage={stage}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />
      </div>
      {selectedRun ? (
        <p className="text-sm text-gray-500">
          v{selectedRun.version} · {selectedRun.status}
        </p>
      ) : null}
      {selectedRun?.status === 'stale' ? (
        <div className="rounded border border-yellow-300 bg-yellow-50 p-3 text-sm text-yellow-800">
          Outdated — an earlier stage was re-run
        </div>
      ) : null}
      {selectedRun?.status === 'failed' && selectedRun.error ? (
        <ErrorBox error={new ApiError(0, selectedRun.error)} />
      ) : null}
      {selectedRun && (selectedRun.status === 'queued' || selectedRun.status === 'running') ? (
        <ProgressBar
          done={progress?.done ?? 0}
          total={progress?.total ?? 0}
          message={progress?.message}
        />
      ) : null}
      <ParamsForm stage={stage} value={params} onChange={setParams} />
      {stage === 'retrieve' && collectionId ? (
        <FilterBuilder
          collectionId={collectionId}
          value={(params as { filters?: PayloadFilter }).filters ?? {}}
          onChange={(filters: PayloadFilter) => setParams({ ...params, filters })}
        />
      ) : null}
      {viewId && artifact != null ? (
        <StageView
          stage={stage}
          stageRunId={viewId}
          artifact={artifact}
          chunks={chunks}
          collectionId={collectionId}
          liveText={liveText}
        />
      ) : null}
      {error ? <ErrorBox error={error} /> : null}
      <button
        type="button"
        className="rounded bg-blue-600 px-3 py-1 text-sm font-medium text-white disabled:opacity-50"
        disabled={starting}
        onClick={() => void start()}
      >
        {`Run ${stage}`}
      </button>
    </section>
  )
}
