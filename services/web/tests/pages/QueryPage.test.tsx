// QueryPage (F-generate): new form on /query (collection select + question + "Ask" (disabled while
// empty) → createQueryRun → navigate to /query/<id>) and the run view on /query/:runId (question
// header + StageStepper transform/retrieve/rerank/generate + "Run all" → runAllQuery with each
// stage's params or lib/defaults). StagePanel is mocked to print stage + liveText.
import { act, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes, useParams } from 'react-router'
import { vi } from 'vitest'

import {
  GENERATE_DEFAULTS,
  RERANK_DEFAULTS,
  RETRIEVE_DEFAULTS,
  TRANSFORM_DEFAULTS,
} from '../../src/lib/defaults'
import { QueryPage } from '../../src/pages/QueryPage'
import { MockEventSource } from '../setup/eventsource'
import { COLLECTION, RUN_ID, stageRun } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'
import { server } from '../setup/server'

vi.mock('../../src/components/StagePanel', () => ({
  StagePanel: (props: { stage: string; liveText?: string | null }) => (
    <div data-testid="stage-panel">
      {props.stage}
      {props.liveText ? ` · ${props.liveText}` : ''}
    </div>
  ),
}))

const QUESTION = 'How did revenue change in Q3?'
const TS = '2026-11-01T18:22:05.123Z'

function queryRun(stages: Record<string, unknown>) {
  return {
    id: RUN_ID,
    collection_id: COLLECTION.id,
    question: QUESTION,
    created_at: TS,
    run_all_pending: [],
    stages: { transform: null, retrieve: null, rerank: null, generate: null, ...stages },
  }
}

/** Target route for navigation assertions (test 1). */
function QueryRouteTarget() {
  const { runId } = useParams()
  return <div>query-route:{runId}</div>
}

test(`/query: collection select + question + 'Ask' → POST /query-runs then navigates to /query/<id>`, async () => {
  let body: unknown = null
  server.use(
    http.get('/api/v1/collections', () => HttpResponse.json({ items: [COLLECTION] })),
    http.post('/api/v1/query-runs', async ({ request }) => {
      body = await request.json()
      return HttpResponse.json(queryRun({}), { status: 201 })
    }),
  )
  const user = userEvent.setup()
  renderWithProviders(
    <Routes>
      <Route path="/query" element={<QueryPage />} />
      <Route path="/query/:runId" element={<QueryRouteTarget />} />
    </Routes>,
    { path: '/query' },
  )
  await screen.findByText('default')
  await user.selectOptions(screen.getByRole('combobox'), COLLECTION.id)
  await user.type(screen.getByRole('textbox'), QUESTION)
  await user.click(screen.getByRole('button', { name: 'Ask' }))
  expect(await screen.findByText(`query-route:${RUN_ID}`)).toBeInTheDocument()
  expect(body).toEqual({ collection_id: COLLECTION.id, question: QUESTION })
})

test(`'Ask' disabled for an empty question`, async () => {
  server.use(http.get('/api/v1/collections', () => HttpResponse.json({ items: [COLLECTION] })))
  const user = userEvent.setup()
  renderWithProviders(<QueryPage />, { path: '/query', route: '/query' })
  await screen.findByText('default')
  expect(screen.getByRole('button', { name: 'Ask' })).toBeDisabled()
  await user.type(screen.getByRole('textbox'), QUESTION)
  expect(screen.getByRole('button', { name: 'Ask' })).toBeEnabled()
})

test(`/query/:runId → question header, stepper transform/retrieve/rerank/generate, 'Run all' → POST /query-runs/<id>/run-all { from_stage: null, params } with TRANSFORM/RETRIEVE/RERANK/GENERATE defaults`, async () => {
  const run = queryRun({})
  let sent: unknown = null
  server.use(
    http.get(`/api/v1/query-runs/${RUN_ID}`, () => HttpResponse.json(run)),
    http.get('/api/v1/collections', () => HttpResponse.json({ items: [COLLECTION] })),
    http.post(`/api/v1/query-runs/${RUN_ID}/run-all`, async ({ request }) => {
      sent = await request.json()
      return HttpResponse.json(run, { status: 202 })
    }),
  )
  const user = userEvent.setup()
  renderWithProviders(<QueryPage />, { path: `/query/${RUN_ID}`, route: '/query/:runId' })
  expect(await screen.findByText(QUESTION)).toBeInTheDocument()
  const stepper = screen.getByRole('navigation', { name: 'Stages' })
  expect(stepper.querySelectorAll('button')).toHaveLength(4)
  for (const stage of ['transform', 'retrieve', 'rerank', 'generate']) {
    expect(within(stepper).getByText(stage)).toBeInTheDocument()
  }
  await user.click(screen.getByRole('button', { name: 'Run all' }))
  await waitFor(() =>
    expect(sent).toEqual({
      from_stage: null,
      params: {
        transform: TRANSFORM_DEFAULTS,
        retrieve: RETRIEVE_DEFAULTS,
        rerank: RERANK_DEFAULTS,
        generate: GENERATE_DEFAULTS,
      },
    }),
  )
})

test(`generate panel receives liveText from generate.token events (vi.mock StagePanel to print liveText)`, async () => {
  const generate = stageRun('generate', { status: 'running' })
  server.use(
    http.get(`/api/v1/query-runs/${RUN_ID}`, () => HttpResponse.json(queryRun({ generate }))),
    http.get('/api/v1/collections', () => HttpResponse.json({ items: [COLLECTION] })),
  )
  const user = userEvent.setup()
  renderWithProviders(<QueryPage />, { path: `/query/${RUN_ID}`, route: '/query/:runId' })
  expect(await screen.findByText(QUESTION)).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: /generate/ }))
  await waitFor(() => expect(MockEventSource.instances).not.toHaveLength(0))
  const token = (index: number, text: string) => ({
    type: 'generate.token',
    run_id: RUN_ID,
    stage_run_id: generate.id,
    stage: 'generate',
    version: 1,
    ts: TS,
    index,
    text,
  })
  act(() => MockEventSource.last().emit('generate.token', token(0, 'Revenue')))
  act(() => MockEventSource.last().emit('generate.token', token(1, ' was')))
  await waitFor(() => expect(screen.getByTestId('stage-panel')).toHaveTextContent('Revenue was'))
})
