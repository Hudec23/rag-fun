import type { FileItem, FileList } from './types'
import { API_BASE, apiFetch } from './client'

/** Query string from the defined filters only; omitted/undefined filters are not sent. */
function toQuery(params: Record<string, string | number | undefined>): string {
  const searchParams = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) searchParams.set(key, String(value))
  }
  const query = searchParams.toString()
  return query ? `?${query}` : ''
}

/** GET /files with optional filters; omitted/undefined filters are not sent. */
export function listFiles(q: {
  limit?: number
  offset?: number
  batch_id?: string
  tag?: string
  mime?: string
}): Promise<FileList> {
  return apiFetch<FileList>(`/files${toQuery(q)}`)
}

export function getFile(id: string): Promise<FileItem> {
  return apiFetch<FileItem>(`/files/${id}`)
}

/** PATCH /files/{id} { tags }. */
export function updateFileTags(id: string, tags: string[]): Promise<FileItem> {
  return apiFetch<FileItem>(`/files/${id}`, { method: 'PATCH', body: { tags } })
}

export function deleteFile(id: string): Promise<void> {
  return apiFetch<void>(`/files/${id}`, { method: 'DELETE' })
}

export function fileContentUrl(id: string): string {
  return `${API_BASE}/files/${id}/content`
}
