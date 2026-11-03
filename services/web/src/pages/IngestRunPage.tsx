/**
 * Route "/ingest/:runId". useIngestRun(runId). Header: filename, collection, "Run all" button
 * (runAllIngest(runId, null, current params of each stage or INGEST_DEFAULTS)) and pending plan chips.
 * <StageStepper> for parse/chunk/embed/store and the selected <StagePanel>. Default selection = first
 * stage not done (else store), computed ONCE when the run first loads; afterwards only the user changes
 * it. The panel gets run = run.stages[stage] and progress = live.progress[that stage run's id]. Passes
 * extra.chunks (from the active chunk artifact) to the embed panel and extra.collectionId to store.
 * Loading/error states as in CollectionsPage.
 */
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useParams } from 'react-router'

import { listStageRuns, runAllIngest } from '../api/runs'
import type {
  ChunkArtifact,
  ChunkParams,
  EmbedParams,
  IngestParamsAll,
  IngestStage,
  IngestRun,
  ParseParams,
} from '../api/types'
import { ErrorBox } from '../components/ErrorBox'
import { StagePanel } from '../components/StagePanel'
import { StageStepper } from '../components/StageStepper'
import { useArtifact } from '../hooks/useArtifact'
import { useCollections } from '../hooks/useCollections'
import { useIngestRun } from '../hooks/useRun'
import { INGEST_DEFAULTS } from '../lib/defaults'

const INGEST_STAGES: IngestStage[] = ['parse', 'chunk', 'embed', 'store']

function stageParams(run: IngestRun, stage: IngestStage): unknown {
  const sr = run.stages[stage]
  if (sr && Object.keys(sr.params).length > 0) return { ...sr.params }
  return { ...INGEST_DEFAULTS[stage] }
}

function runAllParams(run: IngestRun): IngestParamsAll {
  return {
    parse: stageParams(run, 'parse') as ParseParams,
    chunk: stageParams(run, 'chunk') as ChunkParams,
    embed: stageParams(run, 'embed') as EmbedParams,
    store: stageParams(run, 'store') as IngestParamsAll['store'],
  }
}

export function IngestRunPage(): React.ReactElement {
  const { runId = '' } = useParams<{ runId: string }>()
  const { run, error, progress } = useIngestRun(runId)
  const { data: collections } = useCollections()
  const [selected, setSelected] = useState<IngestStage | null>(null)
  // Default selection = first stage not done (else store), pinned once when the run first
  // loads; afterwards only the user (via the stepper) changes the selection.
  const [defaultStage, setDefaultStage] = useState<IngestStage | null>(null)
  useEffect(() => {
    if (defaultStage !== null || !run) return
    // Deferred so the update is not a synchronous setState in this effect.
    void Promise.resolve().then(() => {
      if (defaultStage === null) {
        setDefaultStage(
          INGEST_STAGES.find((stage) => run.stages[stage]?.status !== 'done') ?? 'store',
        )
      }
    })
  }, [run, defaultStage])
  const activeStage = selected ?? defaultStage
  const [runAllError, setRunAllError] = useState<unknown>(null)
  const [running, setRunning] = useState(false)
  const queryClient = useQueryClient()

  // Same key as <StagePanel>/<VersionPicker>: when it becomes enabled it refetches the shared
  // list entry, so live queued/running rows reach the panel.
  const { data: stageRuns } = useQuery({
    queryKey: ['stage-runs', runId, activeStage ?? 'parse'],
    queryFn: () => listStageRuns(runId, activeStage ?? 'parse'),
    enabled: activeStage !== null && Object.keys(progress).length > 0,
  })

  // Progress events may mean the live row appeared/advanced: refresh the stage-run lists.
  const progressKeys = Object.keys(progress).sort().join(',')
  useEffect(() => {
    if (!progressKeys) return
    void queryClient.invalidateQueries({ queryKey: ['stage-runs', runId] })
  }, [progressKeys, queryClient, runId])

  // Run changed via SSE (stage started/completed/failed): refresh the stage-run lists.
  useEffect(() => {
    if (!run) return
    void queryClient.invalidateQueries({ queryKey: ['stage-runs', runId] })
  }, [run, queryClient, runId])

  const chunkRun = run?.stages.chunk ?? null
  const { data: chunkArtifact } = useArtifact<ChunkArtifact>(
    chunkRun?.status === 'done' ? chunkRun.id : null,
  )

  if (error) return <ErrorBox error={error} />
  if (!run) return <p className="p-4 text-sm text-gray-500">Loading…</p>

  const runAll = async () => {
    setRunAllError(null)
    setRunning(true)
    try {
      await runAllIngest(runId, null, runAllParams(run))
      void queryClient.invalidateQueries({ queryKey: ['ingest-run', runId] })
    } catch (err) {
      setRunAllError(err)
    } finally {
      setRunning(false)
    }
  }

  const stageRun = activeStage !== null ? run.stages[activeStage] : null
  const panelRun =
    stageRun ??
    stageRuns?.items.find((item) => item.status === 'running' || item.status === 'queued') ??
    null
  const extra: Record<string, unknown> | undefined =
    activeStage === 'embed'
      ? { chunks: chunkArtifact?.chunks }
      : activeStage === 'store'
        ? { collectionId: run.collection_id }
        : undefined
  const collectionName = collections?.items.find((c) => c.id === run.collection_id)?.name

  return (
    <section className="space-y-3 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-lg font-semibold">{run.file.filename}</h1>
          {collectionName ? <span className="text-sm text-gray-500">{collectionName}</span> : null}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {run.run_all_pending.map((stage) => (
            <span
              key={stage}
              className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800"
            >
              {stage}
            </span>
          ))}
          <button
            type="button"
            className="rounded bg-blue-600 px-3 py-1 text-sm font-medium text-white disabled:opacity-50"
            disabled={running}
            onClick={() => void runAll()}
          >
            Run all
          </button>
        </div>
      </div>
      {runAllError ? <ErrorBox error={runAllError} /> : null}
      <StageStepper
        stages={INGEST_STAGES.map((stage) => ({ name: stage, run: run.stages[stage] }))}
        selected={activeStage ?? ''}
        onSelect={(name: string) => setSelected(name as IngestStage)}
      />
      {activeStage !== null ? (
        <StagePanel
          key={panelRun?.id ?? `pending-${activeStage}`}
          runId={runId}
          runKind="ingest"
          stage={activeStage}
          run={panelRun}
          progress={panelRun ? progress[panelRun.id] : undefined}
          extra={extra}
        />
      ) : null}
    </section>
  )
}
