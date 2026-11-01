import type { FileItem, FileList } from './types'
import { API_BASE } from './client'

/** GET /files with optional filters; omitted/undefined filters are not sent. */
export function listFiles(_q: {
  limit?: number
  offset?: number
  batch_id?: string
  tag?: string
  mime?: string
}): Promise<FileList> {
  throw new Error('not implemented')
}

export function getFile(_id: string): Promise<FileItem> {
  throw new Error('not implemented')
}

/** PATCH /files/{id} { tags }. */
export function updateFileTags(_id: string, _tags: string[]): Promise<FileItem> {
  throw new Error('not implemented')
}

export function deleteFile(_id: string): Promise<void> {
  throw new Error('not implemented')
}

export function fileContentUrl(id: string): string {
  return `${API_BASE}/files/${id}/content`
}
