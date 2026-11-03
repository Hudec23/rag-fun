// StagePanel (F-stage-flow): one stage of a run — params form seeded from run.params or
// lib/defaults, "Run <stage>" button → startIngestStage (ApiError → ErrorBox), progress bar
// while running, stale banner, error box when failed, artifact + stage view when done;
// retrieve stage renders FilterBuilder. ChunkView/FilterBuilder are mocked to sentinels.
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { vi } from 'vitest'

import { StagePanel } from '../../src/components/StagePanel'
import { CHUNK_DEFAULTS } from '../../src/lib/defaults'
import { COLLECTION, CHUNK, RUN_ID, stageRun } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'
import { server } from '../setup/server'

vi.mock('../../src/components/stages/ChunkView', () => ({
  ChunkView: (props: { stageRunId: string }) => <div>{`VIEW ${props.stageRunId}`}</div>,
}))
vi.mock('../../src/components/FilterBuilder', () => ({
  FilterBuilder: () => <div>FILTER_BUILDER</div>,
}))

test('run null (chunk): form seeded with recursive defaults; Run chunk posts { params }', async () => {
  let started: unknown
  server.use(
    http.get('/api/v1/stage-runs', () => HttpResponse.json({ items: [] })),
    http.post(`/api/v1/ingest-runs/${RUN_ID}/stages/chunk`, async ({ request }) => {
      started = await request.json()
      return HttpResponse.json(stageRun('chunk', { status: 'running' }), { status: 202 })
    }),
  )
  const user = userEvent.setup()
  renderWithProviders(<StagePanel runId={RUN_ID} runKind="ingest" stage="chunk" run={null} />)
  expect(screen.getByRole('combobox', { name: 'Strategy' })).toHaveValue('recursive')
  expect(screen.getByLabelText('length')).toHaveValue('1000')
  expect(screen.getByLabelText('overlap')).toHaveValue('100')
  const separators = screen.getByRole('textbox', { name: 'separators' }) as HTMLInputElement
  expect(separators.value).toContain('sentence')
  await user.click(screen.getByRole('button', { name: 'Run chunk' }))
  await waitFor(() => expect(started).toEqual({ params: CHUNK_DEFAULTS.recursive }))
})

test('409 on Run chunk: alert STAGE_PREREQUISITE_MISSING with the contract message', async () => {
  server.use(
    http.get('/api/v1/stage-runs', () => HttpResponse.json({ items: [] })),
    http.post(`/api/v1/ingest-runs/${RUN_ID}/stages/chunk`, () =>
      HttpResponse.json(
        {
          error: {
            code: 'STAGE_PREREQUISITE_MISSING',
            message: 'The previous stage has no done version yet',
            details: { stage: 'chunk', missing: 'parse' },
          },
        },
        { status: 409 },
      ),
    ),
  )
  const user = userEvent.setup()
  renderWithProviders(<StagePanel runId={RUN_ID} runKind="ingest" stage="chunk" run={null} />)
  await user.click(screen.getByRole('button', { name: 'Run chunk' }))
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'STAGE_PREREQUISITE_MISSING: The previous stage has no done version yet',
  )
})

test('running run with progress {1, 2, m}: progressbar 1/2 and the message', () => {
  const running = stageRun('chunk', { status: 'running' })
  server.use(http.get('/api/v1/stage-runs', () => HttpResponse.json({ items: [running] })))
  renderWithProviders(
    <StagePanel
      runId={RUN_ID}
      runKind="ingest"
      stage="chunk"
      run={running}
      progress={{ done: 1, total: 2, message: 'm' }}
    />,
  )
  const bar = screen.getByRole('progressbar')
  expect(bar).toHaveAttribute('aria-valuenow', '1')
  expect(bar).toHaveAttribute('aria-valuemax', '2')
  expect(screen.getByText('1/2')).toBeInTheDocument()
  expect(screen.getByText('m')).toBeInTheDocument()
})

test('failed run: alert PARSE_FAILED with the contract message', async () => {
  const failed = stageRun('parse', {
    status: 'failed',
    error: { code: 'PARSE_FAILED', message: 'Document conversion failed', details: {} },
  })
  server.use(http.get('/api/v1/stage-runs', () => HttpResponse.json({ items: [failed] })))
  renderWithProviders(<StagePanel runId={RUN_ID} runKind="ingest" stage="parse" run={failed} />)
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'PARSE_FAILED: Document conversion failed',
  )
})

test('stale run: banner Outdated — an earlier stage was re-run', () => {
  const stale = stageRun('chunk', { status: 'stale' })
  server.use(http.get('/api/v1/stage-runs', () => HttpResponse.json({ items: [stale] })))
  renderWithProviders(<StagePanel runId={RUN_ID} runKind="ingest" stage="chunk" run={stale} />)
  expect(screen.getByText('Outdated — an earlier stage was re-run')).toBeInTheDocument()
})

test('done run: artifact fetched and ChunkView rendered for the done run id', async () => {
  const done = stageRun('chunk')
  let artifactRequested = false
  server.use(
    http.get('/api/v1/stage-runs', () => HttpResponse.json({ items: [done] })),
    http.get(`/api/v1/stage-runs/${done.id}/artifact`, () => {
      artifactRequested = true
      return HttpResponse.json(CHUNK)
    }),
  )
  renderWithProviders(<StagePanel runId={RUN_ID} runKind="ingest" stage="chunk" run={done} />)
  expect(await screen.findByText(`VIEW ${done.id}`)).toBeInTheDocument()
  expect(artifactRequested).toBe(true)
})

test('retrieve stage: FilterBuilder rendered', async () => {
  server.use(http.get('/api/v1/stage-runs', () => HttpResponse.json({ items: [] })))
  renderWithProviders(
    <StagePanel
      runId={RUN_ID}
      runKind="query"
      stage="retrieve"
      run={null}
      extra={{ collectionId: COLLECTION.id }}
    />,
  )
  expect(await screen.findByText('FILTER_BUILDER')).toBeInTheDocument()
})
