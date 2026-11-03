// IngestRunPage (F-stage-flow): header with filename + "Run all" (run-all POST with each stage's
// current params or INGEST_DEFAULTS), pending plan chips, StageStepper with 4 stages and the
// selected StagePanel (mocked to print the stage). Default selection = first stage not done.
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { vi } from 'vitest'

import { EMBED_DEFAULTS } from '../../src/lib/defaults'
import { IngestRunPage } from '../../src/pages/IngestRunPage'
import { COLLECTION, CHUNK, FILE_ID, RUN_ID, stageRun } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'
import { server } from '../setup/server'

vi.mock('../../src/components/StagePanel', () => ({
  StagePanel: (props: { stage: string }) => <div data-testid="stage-panel">{props.stage}</div>,
}))

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

function runWith(stages: Record<string, unknown>, runAllPending: string[] = []) {
  return {
    id: RUN_ID,
    file: FILE,
    collection_id: COLLECTION.id,
    created_at: '2026-11-01T18:22:05.123Z',
    run_all_pending: runAllPending,
    stages: { parse: null, chunk: null, embed: null, store: null, ...stages },
  }
}

test('header shows filename and Run all; stepper with 4 stages; default selection = first stage not done', async () => {
  const chunk = stageRun('chunk')
  server.use(
    http.get(`/api/v1/ingest-runs/${RUN_ID}`, () =>
      HttpResponse.json(runWith({ parse: stageRun('parse'), chunk })),
    ),
    http.get('/api/v1/collections', () => HttpResponse.json({ items: [COLLECTION] })),
    http.get(`/api/v1/stage-runs/${chunk.id}/artifact`, () => HttpResponse.json(CHUNK)),
  )
  renderWithProviders(<IngestRunPage />, { path: `/ingest/${RUN_ID}`, route: '/ingest/:runId' })
  expect(await screen.findByText('q3-report.pdf')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Run all' })).toBeInTheDocument()
  const stepper = screen.getByRole('navigation', { name: 'Stages' })
  expect(stepper.querySelectorAll('button')).toHaveLength(4)
  // parse and chunk are done, so the default selection is the first stage not done: embed.
  expect(screen.getByTestId('stage-panel')).toHaveTextContent(/^embed$/)
})

test(`'Run all' → POST /ingest-runs/{runId}/run-all { from_stage: null, params } where params uses each stage's current params or INGEST_DEFAULTS`, async () => {
  const parse = stageRun('parse', { params: { strategy: 'plain_text' } })
  const chunk = stageRun('chunk', { params: { strategy: 'sentence', length: 5, overlap: 1 } })
  let sent: unknown = null
  server.use(
    http.get(`/api/v1/ingest-runs/${RUN_ID}`, () => HttpResponse.json(runWith({ parse, chunk }))),
    http.get('/api/v1/collections', () => HttpResponse.json({ items: [COLLECTION] })),
    http.get(`/api/v1/stage-runs/${chunk.id}/artifact`, () => HttpResponse.json(CHUNK)),
    http.post(`/api/v1/ingest-runs/${RUN_ID}/run-all`, async ({ request }) => {
      sent = await request.json()
      return HttpResponse.json(runWith({ parse, chunk }), { status: 202 })
    }),
  )
  const user = userEvent.setup()
  renderWithProviders(<IngestRunPage />, { path: `/ingest/${RUN_ID}`, route: '/ingest/:runId' })
  await user.click(await screen.findByRole('button', { name: 'Run all' }))
  await waitFor(() =>
    expect(sent).toEqual({
      from_stage: null,
      params: {
        parse: { strategy: 'plain_text' },
        chunk: { strategy: 'sentence', length: 5, overlap: 1 },
        embed: { ...EMBED_DEFAULTS },
        store: {},
      },
    }),
  )
})

test(`pending plan chips for run_all_pending ['embed', 'store']`, async () => {
  const chunk = stageRun('chunk')
  server.use(
    http.get(`/api/v1/ingest-runs/${RUN_ID}`, () =>
      HttpResponse.json(runWith({ parse: stageRun('parse'), chunk }, ['embed', 'store'])),
    ),
    http.get('/api/v1/collections', () => HttpResponse.json({ items: [COLLECTION] })),
    http.get(`/api/v1/stage-runs/${chunk.id}/artifact`, () => HttpResponse.json(CHUNK)),
  )
  renderWithProviders(<IngestRunPage />, { path: `/ingest/${RUN_ID}`, route: '/ingest/:runId' })
  await screen.findByText('q3-report.pdf')
  // The default selection (embed) also prints the stage name in the mocked panel: exclude it so
  // each label counts only its occurrences in the header and the stepper.
  const shown = (label: string) =>
    screen.getAllByText(label).filter((el) => !el.closest('[data-testid="stage-panel"]'))
  expect(shown('parse')).toHaveLength(1) // stepper only
  expect(shown('chunk')).toHaveLength(1) // stepper only
  expect(shown('embed')).toHaveLength(2) // stepper + chip
  expect(shown('store')).toHaveLength(2) // stepper + chip
})

test(`selecting 'embed' shows its StagePanel`, async () => {
  server.use(
    http.get(`/api/v1/ingest-runs/${RUN_ID}`, () => HttpResponse.json(runWith({}))),
    http.get('/api/v1/collections', () => HttpResponse.json({ items: [COLLECTION] })),
  )
  const user = userEvent.setup()
  renderWithProviders(<IngestRunPage />, { path: `/ingest/${RUN_ID}`, route: '/ingest/:runId' })
  expect(await screen.findByText('q3-report.pdf')).toBeInTheDocument()
  // Nothing is done, so the default selection is the first stage: parse.
  expect(screen.getByTestId('stage-panel')).toHaveTextContent(/^parse$/)
  await user.click(screen.getByRole('button', { name: /^embed/ }))
  expect(screen.getByTestId('stage-panel')).toHaveTextContent(/^embed$/)
})
