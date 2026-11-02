// F-stage-flow + F-live-progress (UI): stepper, run a stage, live progress via SSE, refetch on events.
import { act, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'

import { IngestRunPage } from '../../src/pages/IngestRunPage'
import { MockEventSource } from '../setup/eventsource'
import { COLLECTION, FILE_ID, PARSE, RUN_ID, stageRun } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'
import { server } from '../setup/server'

const FILE = {
  id: FILE_ID,
  batch_id: '019a4b2c-1e00-7b00-8000-000000000001',
  filename: 'q3-report.pdf',
  mime: 'application/pdf',
  size_bytes: 10,
  sha256: 'a'.repeat(64),
  tags: [],
  created_at: '2026-11-01T18:22:05.123Z',
}

function runWith(stages: Record<string, unknown>) {
  return {
    id: RUN_ID,
    file: FILE,
    collection_id: COLLECTION.id,
    created_at: '2026-11-01T18:22:05.123Z',
    run_all_pending: [],
    stages: { parse: null, chunk: null, embed: null, store: null, ...stages },
  }
}

test('runs parse, shows progress from SSE and the parse view when done', async () => {
  const parse = stageRun('parse', {
    params: { strategy: 'docling_layout', extract_tables: true, page_images: true },
  })
  let current = runWith({})
  let started: unknown = null
  server.use(
    http.get(`/api/v1/ingest-runs/${RUN_ID}`, () => HttpResponse.json(current)),
    http.get('/api/v1/collections', () => HttpResponse.json({ items: [COLLECTION] })),
    http.get('/api/v1/stage-runs', () =>
      HttpResponse.json({ items: current.stages.parse ? [current.stages.parse] : [] }),
    ),
    http.get(`/api/v1/stage-runs/${parse.id}/artifact`, () => HttpResponse.json(PARSE)),
    http.post(`/api/v1/ingest-runs/${RUN_ID}/stages/parse`, async ({ request }) => {
      started = await request.json()
      current = runWith({ parse: { ...parse, status: 'running' } })
      return HttpResponse.json(current.stages.parse, { status: 202 })
    }),
  )
  const user = userEvent.setup()
  renderWithProviders(<IngestRunPage />, { path: `/ingest/${RUN_ID}`, route: '/ingest/:runId' })
  expect(await screen.findByText('q3-report.pdf')).toBeInTheDocument()
  expect(screen.getAllByText('not run')).toHaveLength(4)
  await user.click(screen.getByRole('button', { name: 'Run parse' }))
  await waitFor(() =>
    expect(started).toEqual({
      params: { strategy: 'docling_layout', extract_tables: true, page_images: true },
    }),
  )
  await waitFor(() => expect(MockEventSource.last().url).toBe(`/api/v1/events?run_id=${RUN_ID}`))
  act(() =>
    MockEventSource.last().emit('stage.progress', {
      type: 'stage.progress',
      run_id: RUN_ID,
      stage_run_id: parse.id,
      stage: 'parse',
      version: 1,
      ts: '2026-11-01T18:22:05.123Z',
      done: 1,
      total: 2,
      message: 'OCR page 1/2',
    }),
  )
  expect(await screen.findByRole('progressbar')).toHaveAttribute('aria-valuenow', '1')
  expect(screen.getByText('OCR page 1/2')).toBeInTheDocument()
  current = runWith({ parse })
  act(() =>
    MockEventSource.last().emit('stage.completed', {
      type: 'stage.completed',
      run_id: RUN_ID,
      stage_run_id: parse.id,
      stage: 'parse',
      version: 1,
      ts: '2026-11-01T18:22:06.123Z',
      artifact_key: 'k',
      summary: { stage: 'parse' },
    }),
  )
  expect(await screen.findByText('2 pages · 8 elements · 0 tables')).toBeInTheDocument()
})

test('shows stale and prerequisite errors', async () => {
  const chunkStale = stageRun('chunk', {
    status: 'stale',
    params: { strategy: 'recursive', length: 300, overlap: 30, separators: ['\n\n'] },
  })
  server.use(
    http.get(`/api/v1/ingest-runs/${RUN_ID}`, () =>
      HttpResponse.json(runWith({ parse: stageRun('parse'), chunk: chunkStale })),
    ),
    http.get('/api/v1/collections', () => HttpResponse.json({ items: [COLLECTION] })),
    http.get('/api/v1/stage-runs', () => HttpResponse.json({ items: [chunkStale] })),
    http.get('/api/v1/stage-runs/:id/artifact', () => HttpResponse.json({})),
    http.post(`/api/v1/ingest-runs/${RUN_ID}/stages/embed`, () =>
      HttpResponse.json(
        {
          error: {
            code: 'STAGE_PREREQUISITE_MISSING',
            message: 'The previous stage has no done version yet',
            details: { stage: 'embed', missing: 'chunk' },
          },
        },
        { status: 409 },
      ),
    ),
  )
  const user = userEvent.setup()
  renderWithProviders(<IngestRunPage />, { path: `/ingest/${RUN_ID}`, route: '/ingest/:runId' })
  await user.click(await screen.findByRole('button', { name: /^chunk/ }))
  expect(await screen.findByText('Outdated — an earlier stage was re-run')).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: /^embed/ }))
  await user.click(screen.getByRole('button', { name: 'Run embed' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('STAGE_PREREQUISITE_MISSING')
})
