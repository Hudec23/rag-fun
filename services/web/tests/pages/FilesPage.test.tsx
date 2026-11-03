// FilesPage: batches listed with their file rows, per-file ingest/delete, whole-batch ingest.
import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes, useParams } from 'react-router'
import { vi } from 'vitest'

import type { Batch, FileItem, IngestRun } from '../../src/api/types'
import { INGEST_DEFAULTS } from '../../src/lib/defaults'
import { FilesPage } from '../../src/pages/FilesPage'
import { COLLECTION, FILE_ID, RUN_ID } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'
import { server } from '../setup/server'

const BATCH_ID = '019a4b2c-1e00-7b00-8000-000000000001'
const BATCH: Batch = {
  id: BATCH_ID,
  name: 'Q3 reports',
  tags: ['finance'],
  file_count: 2,
  created_at: '2026-11-01T18:22:05.123Z',
}
const FILE: FileItem = {
  id: FILE_ID,
  batch_id: BATCH_ID,
  filename: 'q3-report.pdf',
  mime: 'application/pdf',
  size_bytes: 482113,
  sha256: 'a'.repeat(64),
  tags: [],
  created_at: '2026-11-01T18:22:05.123Z',
}
const FILE_2: FileItem = {
  id: '019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a02',
  batch_id: BATCH_ID,
  filename: 'notes.md',
  mime: 'text/markdown',
  size_bytes: 512,
  sha256: 'b'.repeat(64),
  tags: [],
  created_at: '2026-11-01T18:22:05.123Z',
}
const BATCH_LIST = {
  items: [BATCH],
  page: { total: 1, limit: 50, offset: 0 },
}
const FILES_LIST = {
  items: [FILE, FILE_2],
  page: { total: 2, limit: 50, offset: 0 },
}

function ingestRun(id: string, file: FileItem): IngestRun {
  return {
    id,
    file,
    collection_id: COLLECTION.id,
    created_at: '2026-11-01T18:22:05.123Z',
    run_all_pending: [],
    stages: { parse: null, chunk: null, embed: null, store: null },
  }
}

/** GETs every FilesPage test needs on load: collections (for the ingest selects), the batch list,
 *  and the files (both per-batch and flat endpoints — the page may use either). */
function commonHandlers() {
  return [
    http.get('/api/v1/collections', () => HttpResponse.json({ items: [COLLECTION] })),
    http.get('/api/v1/batches', () => HttpResponse.json(BATCH_LIST)),
    http.get('/api/v1/batches/:id', () =>
      HttpResponse.json({ batch: BATCH, files: [FILE, FILE_2] }),
    ),
    http.get('/api/v1/files', () => HttpResponse.json(FILES_LIST)),
  ]
}

/** Target route for navigation assertions (test 2). */
function IngestRouteTarget() {
  const { runId } = useParams()
  return <div>ingest-route:{runId}</div>
}

test('lists batches with file rows (filename, type, size)', async () => {
  server.use(...commonHandlers())
  renderWithProviders(<FilesPage />)
  expect(await screen.findByText('Q3 reports')).toBeInTheDocument()
  expect(screen.getByText('finance')).toBeInTheDocument()
  expect(await screen.findByText('q3-report.pdf')).toBeInTheDocument()
  expect(screen.getByText('application/pdf')).toBeInTheDocument()
  expect(screen.getByText('470.8 KB')).toBeInTheDocument()
  expect(screen.getByText('notes.md')).toBeInTheDocument()
})

test('ingests a file via "Ingest…" and navigates to the run', async () => {
  let body: unknown = null
  server.use(
    ...commonHandlers(),
    http.post('/api/v1/ingest-runs', async ({ request }) => {
      body = await request.json()
      return HttpResponse.json(ingestRun(RUN_ID, FILE), { status: 201 })
    }),
  )
  const user = userEvent.setup()
  renderWithProviders(
    <Routes>
      <Route path="/" element={<FilesPage />} />
      <Route path="/ingest/:runId" element={<IngestRouteTarget />} />
    </Routes>,
  )
  const row = (await screen.findByText('q3-report.pdf')).closest('tr')!
  await user.click(within(row).getByRole('button', { name: 'Ingest…' }))
  await user.selectOptions(within(row).getByRole('combobox'), COLLECTION.id)
  await user.click(within(row).getByRole('button', { name: 'Start' }))
  expect(await screen.findByText(`ingest-route:${RUN_ID}`)).toBeInTheDocument()
  expect(body).toEqual({ file_id: FILE_ID, collection_id: COLLECTION.id })
})

test('deletes a file after confirm', async () => {
  let deleted: string | null = null
  server.use(
    ...commonHandlers(),
    http.delete(`/api/v1/files/${FILE_ID}`, () => {
      deleted = FILE_ID
      return new HttpResponse(null, { status: 204 })
    }),
  )
  const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)
  const user = userEvent.setup()
  renderWithProviders(<FilesPage />)
  const row = (await screen.findByText('q3-report.pdf')).closest('tr')!
  await user.click(within(row).getByRole('button', { name: 'Delete' }))
  await waitFor(() => expect(deleted).toBe(FILE_ID))
  expect(confirmSpy).toHaveBeenCalledTimes(1)
  confirmSpy.mockRestore()
})

test('ingests a batch with INGEST_DEFAULTS and lists the runs', async () => {
  const RUN_B = ingestRun('019a4b2c-2000-7c00-9000-00000000000b', FILE_2)
  let body: unknown = null
  server.use(
    ...commonHandlers(),
    http.post(`/api/v1/batches/${BATCH_ID}/ingest`, async ({ request }) => {
      body = await request.json()
      return HttpResponse.json({ items: [ingestRun(RUN_ID, FILE), RUN_B] }, { status: 202 })
    }),
  )
  const user = userEvent.setup()
  renderWithProviders(<FilesPage />)
  await screen.findByText('Q3 reports')
  await user.click(screen.getByRole('button', { name: 'Ingest batch' }))
  await user.selectOptions(screen.getByRole('combobox'), COLLECTION.id)
  expect(await screen.findByText('2 runs started')).toBeInTheDocument()
  expect(body).toEqual({ collection_id: COLLECTION.id, params: INGEST_DEFAULTS })
  const hrefs = screen.getAllByRole('link').map((link) => link.getAttribute('href'))
  expect(hrefs).toEqual(expect.arrayContaining([`/ingest/${RUN_ID}`, `/ingest/${RUN_B.id}`]))
})
