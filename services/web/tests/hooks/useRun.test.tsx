// Hook tests for src/hooks/useRun.ts: renderHook inside a QueryClientProvider (fresh client,
// no retries), msw counts the run fetches and MockEventSource.last().emit(type, data)
// delivers SSE events. Instances are reset after every test (tests/setup/setup.ts).
import { act, renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import type { ReactNode } from 'react'

import type { RunEvent } from '../../src/api/types'
import { useIngestRun, useQueryRun } from '../../src/hooks/useRun'
import { COLLECTION, FILE_ID, RUN_ID, stageRun } from '../setup/fixtures'
import { MockEventSource } from '../setup/eventsource'
import { server } from '../setup/server'

const TS = '2026-11-01T18:22:05.123Z'

const PARSE_RUN = stageRun('parse')
const GENERATE_RUN = stageRun('generate')

const FILE = {
  id: FILE_ID,
  batch_id: '019a4b2c-1e00-7b00-8000-000000000001',
  filename: 'q3-report.pdf',
  mime: 'application/pdf',
  size_bytes: 10,
  sha256: 'a'.repeat(64),
  tags: [],
  created_at: TS,
}

function ingestRunData(stages: Record<string, unknown>) {
  return {
    id: RUN_ID,
    file: FILE,
    collection_id: COLLECTION.id,
    created_at: TS,
    run_all_pending: [],
    stages: { parse: null, chunk: null, embed: null, store: null, ...stages },
  }
}

function queryRunData(stages: Record<string, unknown>) {
  return {
    id: RUN_ID,
    collection_id: COLLECTION.id,
    question: 'What does the report say?',
    created_at: TS,
    run_all_pending: [],
    stages: { transform: null, retrieve: null, rerank: null, generate: null, ...stages },
  }
}

const COMPLETED: RunEvent = {
  type: 'stage.completed',
  run_id: RUN_ID,
  stage_run_id: PARSE_RUN.id,
  stage: 'parse',
  version: 1,
  ts: TS,
  artifact_key: `${RUN_ID}/parse/v1.json`,
  summary: { pages: 2 },
}

function updated(runKind: 'ingest' | 'query'): RunEvent {
  return {
    type: 'run.updated',
    run_id: RUN_ID,
    run_kind: runKind,
    reason: 'stage completed',
    ts: TS,
  }
}

function renderRun<T>(render: () => T) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return renderHook(render, {
    wrapper: ({ children }: { children?: ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    ),
  })
}

test('useIngestRun(RUN_ID) fetches GET /api/v1/ingest-runs/RUN_ID and exposes run', async () => {
  const run = ingestRunData({ parse: PARSE_RUN })
  let calls = 0
  server.use(
    http.get(`/api/v1/ingest-runs/${RUN_ID}`, () => {
      calls += 1
      return HttpResponse.json(run)
    }),
  )
  const { result } = renderRun(() => useIngestRun(RUN_ID))
  await waitFor(() => expect(result.current.run).toEqual(run))
  expect(calls).toBe(1)
  expect(result.current.progress).toEqual({})
  expect(result.current.tokens).toEqual({})
})

test('stage.completed event refetches the run (msw handler called twice)', async () => {
  const first = ingestRunData({})
  const second = ingestRunData({ parse: PARSE_RUN })
  let calls = 0
  server.use(
    http.get(`/api/v1/ingest-runs/${RUN_ID}`, () => {
      calls += 1
      return HttpResponse.json(calls === 1 ? first : second)
    }),
  )
  const { result } = renderRun(() => useIngestRun(RUN_ID))
  await waitFor(() => expect(result.current.run).toEqual(first))
  await waitFor(() => expect(MockEventSource.instances).toHaveLength(1))
  act(() => MockEventSource.last().emit('stage.completed', COMPLETED))
  await waitFor(() => expect(calls).toBe(2))
  await waitFor(() => expect(result.current.run).toEqual(second))
})

test('stage.progress event updates the progress map without refetching', async () => {
  const run = ingestRunData({})
  let calls = 0
  server.use(
    http.get(`/api/v1/ingest-runs/${RUN_ID}`, () => {
      calls += 1
      return HttpResponse.json(run)
    }),
  )
  const { result } = renderRun(() => useIngestRun(RUN_ID))
  await waitFor(() => expect(result.current.run).toEqual(run))
  act(() =>
    MockEventSource.last().emit('stage.progress', {
      type: 'stage.progress',
      run_id: RUN_ID,
      stage_run_id: 's',
      stage: 'parse',
      version: 1,
      ts: TS,
      done: 1,
      total: 3,
      message: 'm',
    }),
  )
  await waitFor(() =>
    expect(result.current.progress).toEqual({ s: { done: 1, total: 3, message: 'm' } }),
  )
  expect(calls).toBe(1)
})

test('useQueryRun joins generate.token texts in index order, even when out of order', async () => {
  const run = queryRunData({})
  server.use(http.get(`/api/v1/query-runs/${RUN_ID}`, () => HttpResponse.json(run)))
  const { result } = renderRun(() => useQueryRun(RUN_ID))
  await waitFor(() => expect(result.current.run).toEqual(run))
  const stageRunId = GENERATE_RUN.id
  const token = (index: number, text: string): RunEvent => ({
    type: 'generate.token',
    run_id: RUN_ID,
    stage_run_id: stageRunId,
    stage: 'generate',
    version: 1,
    ts: TS,
    index,
    text,
  })
  act(() => MockEventSource.last().emit('generate.token', token(1, 'lo')))
  act(() => MockEventSource.last().emit('generate.token', token(0, 'Hel')))
  await waitFor(() => expect(result.current.tokens).toEqual({ [stageRunId]: 'Hello' }))
})

test('run.updated event refetches the run (msw handler called twice)', async () => {
  const first = queryRunData({})
  const second = queryRunData({ generate: GENERATE_RUN })
  let calls = 0
  server.use(
    http.get(`/api/v1/query-runs/${RUN_ID}`, () => {
      calls += 1
      return HttpResponse.json(calls === 1 ? first : second)
    }),
  )
  const { result } = renderRun(() => useQueryRun(RUN_ID))
  await waitFor(() => expect(result.current.run).toEqual(first))
  await waitFor(() => expect(MockEventSource.instances).toHaveLength(1))
  act(() => MockEventSource.last().emit('run.updated', updated('query')))
  await waitFor(() => expect(calls).toBe(2))
  await waitFor(() => expect(result.current.run).toEqual(second))
})
