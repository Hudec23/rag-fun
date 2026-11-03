/**
 * Route "/query" (new) and "/query/:runId". New: collection select + question textarea + "Ask" (disabled
 * while the question is empty) → createQueryRun → navigate to /query/<id>. With runId: useQueryRun;
 * header with the question and "Run all" → runAllQuery(runId, null, {transform, retrieve, rerank,
 * generate} = each stage's current params or lib/defaults); <StageStepper> transform/retrieve/rerank/
 * generate + selected <StagePanel> (generate gets liveText = live.tokens[generate stage run id]).
 */
import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router'

import { createQueryRun, runAllQuery } from '../api/runs'
import type {
  GenerateParams,
  QueryRun,
  QueryStage,
  RerankParams,
  RetrieveParams,
  TransformParams,
} from '../api/types'
import { ErrorBox } from '../components/ErrorBox'
import { StagePanel } from '../components/StagePanel'
import { StageStepper } from '../components/StageStepper'
import { useCollections } from '../hooks/useCollections'
import { useQueryRun } from '../hooks/useRun'
import {
  GENERATE_DEFAULTS,
  RERANK_DEFAULTS,
  RETRIEVE_DEFAULTS,
  TRANSFORM_DEFAULTS,
} from '../lib/defaults'

const QUERY_STAGES: QueryStage[] = ['transform', 'retrieve', 'rerank', 'generate']

const QUERY_DEFAULTS: Record<QueryStage, object> = {
  transform: TRANSFORM_DEFAULTS,
  retrieve: RETRIEVE_DEFAULTS,
  rerank: RERANK_DEFAULTS,
  generate: GENERATE_DEFAULTS,
}

function stageParams(run: QueryRun, stage: QueryStage): unknown {
  const sr = run.stages[stage]
  if (sr && Object.keys(sr.params).length > 0) return { ...sr.params }
  return { ...QUERY_DEFAULTS[stage] }
}

function runAllParams(run: QueryRun) {
  return {
    transform: stageParams(run, 'transform') as TransformParams,
    retrieve: stageParams(run, 'retrieve') as RetrieveParams,
    rerank: stageParams(run, 'rerank') as RerankParams,
    generate: stageParams(run, 'generate') as GenerateParams,
  }
}

/** New query: collection select + question textarea + "Ask" (disabled while empty) → createQueryRun →
 * navigate to /query/<id>. Loading/error states as in CollectionsPage. */
function NewQueryForm(): React.ReactElement {
  const navigate = useNavigate()
  const { data, error, isLoading } = useCollections()
  const [collectionId, setCollectionId] = useState('')
  const [question, setQuestion] = useState('')
  const [submitError, setSubmitError] = useState<unknown>(null)
  const [submitting, setSubmitting] = useState(false)

  const submit = async () => {
    if (question.trim() === '' || submitting) return
    setSubmitError(null)
    setSubmitting(true)
    try {
      const run = await createQueryRun(collectionId, question)
      navigate(`/query/${run.id}`)
    } catch (err) {
      setSubmitError(err)
      setSubmitting(false)
    }
  }

  if (isLoading) return <p className="p-4 text-sm text-gray-500">Loading…</p>
  if (error) return <ErrorBox error={error} />

  return (
    <section className="space-y-3 p-4">
      <h1 className="text-lg font-semibold">New query</h1>
      <select
        aria-label="Collection"
        value={collectionId}
        onChange={(event) => setCollectionId(event.target.value)}
        className="rounded border border-gray-300 bg-white px-2 py-1 text-sm"
      >
        <option value="">Collection…</option>
        {data!.items.map((collection) => (
          <option key={collection.id} value={collection.id}>
            {collection.name}
          </option>
        ))}
      </select>
      <textarea
        aria-label="Question"
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        rows={3}
        className="w-full rounded border border-gray-300 bg-white px-2 py-1 text-sm"
      />
      {submitError ? <ErrorBox error={submitError} /> : null}
      <button
        type="button"
        className="rounded bg-blue-600 px-3 py-1 text-sm font-medium text-white disabled:opacity-50"
        disabled={question.trim() === '' || submitting}
        onClick={() => void submit()}
      >
        Ask
      </button>
    </section>
  )
}

/** "/query/:runId": question header + "Run all" → runAllQuery with each stage's current params or
 * lib/defaults; <StageStepper> transform/retrieve/rerank/generate and the selected <StagePanel>
 * (generate gets liveText = tokens[that stage run's id]). Default selection = first stage not done
 * (else generate), computed ONCE when the run first loads; afterwards only the user changes it. */
function QueryRunView({ runId }: { runId: string }): React.ReactElement {
  const { run, error, progress, tokens } = useQueryRun(runId)
  const { data: collections } = useCollections()
  const [selected, setSelected] = useState<QueryStage | null>(null)
  const [defaultStage, setDefaultStage] = useState<QueryStage | null>(null)
  useEffect(() => {
    if (defaultStage !== null || !run) return
    // Deferred so the update is not a synchronous setState in this effect.
    void Promise.resolve().then(() => {
      if (defaultStage === null) {
        setDefaultStage(
          QUERY_STAGES.find((stage) => run.stages[stage]?.status !== 'done') ?? 'generate',
        )
      }
    })
  }, [run, defaultStage])
  const activeStage = selected ?? defaultStage
  const [runAllError, setRunAllError] = useState<unknown>(null)
  const [running, setRunning] = useState(false)
  const queryClient = useQueryClient()

  if (error) return <ErrorBox error={error} />
  if (!run) return <p className="p-4 text-sm text-gray-500">Loading…</p>

  const runAll = async () => {
    setRunAllError(null)
    setRunning(true)
    try {
      await runAllQuery(runId, null, runAllParams(run))
      void queryClient.invalidateQueries({ queryKey: ['query-run', runId] })
    } catch (err) {
      setRunAllError(err)
    } finally {
      setRunning(false)
    }
  }

  const stageRun = activeStage !== null ? run.stages[activeStage] : null
  const generateRun = run.stages.generate
  const extra: Record<string, unknown> | undefined =
    activeStage === 'retrieve' ? { collectionId: run.collection_id } : undefined
  const collectionName = collections?.items.find((c) => c.id === run.collection_id)?.name

  return (
    <section className="space-y-3 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-lg font-semibold">{run.question}</h1>
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
        stages={QUERY_STAGES.map((stage) => ({ name: stage, run: run.stages[stage] }))}
        selected={activeStage ?? ''}
        onSelect={(name: string) => setSelected(name as QueryStage)}
      />
      {activeStage !== null ? (
        <StagePanel
          key={stageRun?.id ?? `pending-${activeStage}`}
          runId={runId}
          runKind="query"
          stage={activeStage}
          run={stageRun}
          progress={stageRun ? progress[stageRun.id] : undefined}
          liveText={
            activeStage === 'generate' && generateRun ? (tokens[generateRun.id] ?? null) : null
          }
          extra={extra}
        />
      ) : null}
    </section>
  )
}

export function QueryPage(): React.ReactElement {
  const { runId } = useParams<{ runId: string }>()
  return runId ? <QueryRunView runId={runId} /> : <NewQueryForm />
}
