// F-upload + F-tags (UI): upload a batch with tags, see it listed, edit file tags.
import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'

import { FilesPage } from '../../src/pages/FilesPage'
import { COLLECTION, FILE_ID } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'
import { server } from '../setup/server'

const BATCH = {
  id: '019a4b2c-1e00-7b00-8000-000000000001',
  name: 'Q3 reports',
  tags: ['finance'],
  file_count: 1,
  created_at: '2026-11-01T18:22:05.123Z',
}
const FILE = {
  id: FILE_ID,
  batch_id: BATCH.id,
  filename: 'q3-report.pdf',
  mime: 'application/pdf',
  size_bytes: 482113,
  sha256: 'a'.repeat(64),
  tags: [],
  created_at: '2026-11-01T18:22:05.123Z',
}

test('uploads files as one batch with tags and lists it', async () => {
  let uploaded: FormData | null = null
  let batches = [] as (typeof BATCH)[]
  server.use(
    http.get('/api/v1/collections', () => HttpResponse.json({ items: [COLLECTION] })),
    http.get('/api/v1/batches', () =>
      HttpResponse.json({ items: batches, page: { total: batches.length, limit: 50, offset: 0 } }),
    ),
    http.get('/api/v1/batches/:id', () => HttpResponse.json({ batch: BATCH, files: [FILE] })),
    http.get('/api/v1/files', () =>
      HttpResponse.json({ items: [FILE], page: { total: 1, limit: 50, offset: 0 } }),
    ),
    http.post('/api/v1/batches', async ({ request }) => {
      uploaded = await request.formData()
      batches = [BATCH]
      return HttpResponse.json({ batch: BATCH, files: [FILE] }, { status: 201 })
    }),
  )
  const user = userEvent.setup()
  renderWithProviders(<FilesPage />)
  const input = screen.getByLabelText('Choose files')
  await user.upload(input, [
    new File(['%PDF'], 'q3-report.pdf', { type: 'application/pdf' }),
    new File(['# h'], 'notes.md'),
  ])
  await user.type(screen.getByLabelText('Add tag'), 'finance{Enter}')
  await user.click(screen.getByRole('button', { name: 'Upload 2 files' }))
  await waitFor(() => expect(uploaded).not.toBeNull())
  expect(uploaded!.getAll('files')).toHaveLength(2)
  expect(uploaded!.get('tags')).toBe('finance')
  expect(await screen.findByText('q3-report.pdf')).toBeInTheDocument()
  expect(screen.getByText('Q3 reports')).toBeInTheDocument()
})

test('editing a file tag patches the file', async () => {
  let patched: unknown = null
  server.use(
    http.get('/api/v1/collections', () => HttpResponse.json({ items: [COLLECTION] })),
    http.get('/api/v1/batches', () =>
      HttpResponse.json({ items: [BATCH], page: { total: 1, limit: 50, offset: 0 } }),
    ),
    http.get('/api/v1/batches/:id', () => HttpResponse.json({ batch: BATCH, files: [FILE] })),
    http.get('/api/v1/files', () =>
      HttpResponse.json({ items: [FILE], page: { total: 1, limit: 50, offset: 0 } }),
    ),
    http.patch(`/api/v1/files/${FILE_ID}`, async ({ request }) => {
      patched = await request.json()
      return HttpResponse.json({ ...FILE, tags: ['legal'] })
    }),
  )
  const user = userEvent.setup()
  renderWithProviders(<FilesPage />)
  const row = (await screen.findByText('q3-report.pdf')).closest('tr')!
  await user.type(within(row).getByLabelText('Add tag'), 'legal{Enter}')
  await waitFor(() => expect(patched).toEqual({ tags: ['legal'] }))
})
