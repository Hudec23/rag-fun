// VersionPicker (F-stage-flow): <select aria-label="Version"> listing listStageRuns(runId, stage)
// items as "v<version> · <status>", newest first; change → onSelect(id); hidden when < 2 versions.
import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { vi } from 'vitest'

import { VersionPicker } from '../../src/components/VersionPicker'
import { RUN_ID, stageRun } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'
import { server } from '../setup/server'

test('fetches the stage runs by run_id and stage and lists v2 · done then v1 · failed', async () => {
  const v2 = stageRun('parse', { version: 2 })
  const v1 = stageRun('parse', { status: 'failed' })
  let url: string | null = null
  server.use(
    http.get('/api/v1/stage-runs', ({ request }) => {
      url = request.url
      return HttpResponse.json({ items: [v2, v1] })
    }),
  )
  renderWithProviders(
    <VersionPicker runId={RUN_ID} stage="parse" selectedId={v2.id} onSelect={vi.fn()} />,
  )
  const select = await screen.findByRole('combobox', { name: 'Version' })
  expect(
    within(select)
      .getAllByRole('option')
      .map((option) => option.textContent),
  ).toEqual(['v2 · done', 'v1 · failed'])
  const query = new URL(url!, window.location.origin).searchParams
  expect(query.get('run_id')).toBe(RUN_ID)
  expect(query.get('stage')).toBe('parse')
})

test('calls onSelect with the v1 id when v1 · failed is chosen', async () => {
  const v2 = stageRun('parse', { version: 2 })
  const v1 = stageRun('parse', { status: 'failed' })
  server.use(http.get('/api/v1/stage-runs', () => HttpResponse.json({ items: [v2, v1] })))
  const onSelect = vi.fn()
  const user = userEvent.setup()
  renderWithProviders(
    <VersionPicker runId={RUN_ID} stage="parse" selectedId={v2.id} onSelect={onSelect} />,
  )
  const select = await screen.findByRole('combobox', { name: 'Version' })
  await user.selectOptions(select, within(select).getByRole('option', { name: 'v1 · failed' }))
  expect(onSelect).toHaveBeenCalledTimes(1)
  expect(onSelect).toHaveBeenCalledWith(v1.id)
})

test('renders nothing when the stage has only one version', async () => {
  server.use(
    http.get('/api/v1/stage-runs', () => HttpResponse.json({ items: [stageRun('parse')] })),
  )
  const { client } = renderWithProviders(
    <VersionPicker runId={RUN_ID} stage="parse" selectedId={null} onSelect={vi.fn()} />,
  )
  await waitFor(() => {
    const queries = client.getQueryCache().getAll()
    expect(queries.length).toBeGreaterThan(0)
    expect(queries.every((query) => query.state.status !== 'pending')).toBe(true)
  })
  expect(screen.queryByRole('combobox', { name: 'Version' })).not.toBeInTheDocument()
})
