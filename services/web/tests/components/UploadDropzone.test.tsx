// UploadDropzone (F-upload): file selection, batch name + tags upload, API error handling.
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { vi } from 'vitest'

import type { Batch, BatchWithFiles, FileItem } from '../../src/api/types'
import { UploadDropzone } from '../../src/components/UploadDropzone'
import { FILE_ID } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'
import { server } from '../setup/server'

const BATCH_ID = '019a4b2c-1e00-7b00-8000-000000000001'
const CREATED_AT = '2026-11-01T18:22:05.123Z'

const BATCH: Batch = {
  id: BATCH_ID,
  name: 'Quarterly',
  tags: ['hr'],
  file_count: 2,
  created_at: CREATED_AT,
}
const FILE_A: FileItem = {
  id: FILE_ID,
  batch_id: BATCH_ID,
  filename: 'report.pdf',
  mime: 'application/pdf',
  size_bytes: 482113,
  sha256: 'a'.repeat(64),
  tags: [],
  created_at: CREATED_AT,
}
const FILE_B: FileItem = {
  id: '019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a02',
  batch_id: BATCH_ID,
  filename: 'notes.md',
  mime: 'text/markdown',
  size_bytes: 12,
  sha256: 'b'.repeat(64),
  tags: [],
  created_at: CREATED_AT,
}
const BATCH_WITH_FILES: BatchWithFiles = { batch: BATCH, files: [FILE_A, FILE_B] }

test('lists selected files and enables the upload button, disabled with 0 files', async () => {
  const user = userEvent.setup()
  renderWithProviders(<UploadDropzone onUploaded={vi.fn()} />)
  expect(screen.getByRole('button', { name: 'Upload 0 files' })).toBeDisabled()
  const input = screen.getByLabelText('Choose files')
  await user.upload(input, [
    new File(['%PDF'], 'report.pdf', { type: 'application/pdf' }),
    new File(['# h'], 'notes.md'),
  ])
  expect(screen.getByText('report.pdf')).toBeInTheDocument()
  expect(screen.getByText('notes.md')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Upload 2 files' })).toBeEnabled()
})

test('posts the batch name and tags and calls onUploaded with the batch id, clearing the selection', async () => {
  let uploaded: FormData | null = null
  server.use(
    http.post('/api/v1/batches', async ({ request }) => {
      uploaded = await request.formData()
      return HttpResponse.json(BATCH_WITH_FILES, { status: 201 })
    }),
  )
  const onUploaded = vi.fn()
  const user = userEvent.setup()
  renderWithProviders(<UploadDropzone onUploaded={onUploaded} />)
  const input = screen.getByLabelText('Choose files')
  await user.upload(input, [
    new File(['%PDF'], 'report.pdf', { type: 'application/pdf' }),
    new File(['# h'], 'notes.md'),
  ])
  await user.type(screen.getByLabelText('Batch name'), 'Quarterly')
  await user.type(screen.getByLabelText('Add tag'), 'hr{Enter}')
  await user.click(screen.getByRole('button', { name: 'Upload 2 files' }))
  await waitFor(() => expect(onUploaded).toHaveBeenCalledTimes(1))
  expect(onUploaded).toHaveBeenCalledWith(BATCH_ID)
  expect(uploaded).not.toBeNull()
  expect(uploaded!.getAll('files')).toHaveLength(2)
  expect(uploaded!.get('name')).toBe('Quarterly')
  expect(uploaded!.get('tags')).toBe('hr')
  expect(screen.queryByText('report.pdf')).not.toBeInTheDocument()
  expect(screen.queryByText('notes.md')).not.toBeInTheDocument()
})

test('shows an alert with the error code and keeps the selection when the upload returns 415', async () => {
  server.use(
    http.post('/api/v1/batches', () =>
      HttpResponse.json(
        {
          error: {
            code: 'UNSUPPORTED_FILE_TYPE',
            message: 'File type is not supported',
            details: {},
          },
        },
        { status: 415 },
      ),
    ),
  )
  const onUploaded = vi.fn()
  const user = userEvent.setup()
  renderWithProviders(<UploadDropzone onUploaded={onUploaded} />)
  const input = screen.getByLabelText('Choose files')
  await user.upload(input, [
    new File(['%PDF'], 'report.pdf', { type: 'application/pdf' }),
    new File(['# h'], 'notes.md'),
  ])
  await user.click(screen.getByRole('button', { name: 'Upload 2 files' }))
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'UNSUPPORTED_FILE_TYPE: File type is not supported',
  )
  expect(screen.getByText('report.pdf')).toBeInTheDocument()
  expect(screen.getByText('notes.md')).toBeInTheDocument()
  expect(onUploaded).not.toHaveBeenCalled()
})
