import type {
  BatchList,
  BatchWithFiles,
  Batch,
  ErrorBody,
  IngestParamsAll,
  IngestRun,
} from './types'
import { API_BASE, ApiError, apiFetch } from './client'

/** Fixed multipart boundary: deterministic, and distinctive enough that file content will not
 * collide with it in practice. */
const MULTIPART_BOUNDARY = 'ragfun-upload-boundary'

function multipartField(header: string, value: string): Uint8Array {
  return new TextEncoder().encode(
    `--${MULTIPART_BOUNDARY}\r\nContent-Disposition: form-data; name="${header}"\r\n\r\n${value}\r\n`,
  )
}

function multipartFilePart(file: File, content: Uint8Array): Uint8Array[] {
  const encoder = new TextEncoder()
  const header =
    `--${MULTIPART_BOUNDARY}\r\n` +
    `Content-Disposition: form-data; name="files"; filename="${file.name}"\r\n` +
    `Content-Type: ${file.type || 'application/octet-stream'}\r\n\r\n`
  return [encoder.encode(header), content, encoder.encode('\r\n')]
}

/** POST a hand-crafted multipart body.
 *
 * In the jsdom test environment the global File is jsdom's, while Node's fetch (and the in-process
 * msw handler, which parses the multipart body) only accepts the native File from node:buffer. So
 * while fetch is in flight we temporarily install the native File and restore the old one in a
 * finally. In the browser node:buffer is not available and the plain fetch path is used. */
async function fetchMultipart(url: string, body: Uint8Array<ArrayBuffer>): Promise<Response> {
  const options: RequestInit = {
    method: 'POST',
    headers: { 'Content-Type': `multipart/form-data; boundary=${MULTIPART_BOUNDARY}` },
    body,
  }
  // The non-literal specifier keeps tsc from resolving node:buffer (it is untyped in this
  // project) and Vite still externalizes the import to an empty module in the browser, where
  // File is undefined and the plain fetch path is taken.
  let nativeFile: typeof File | undefined
  try {
    nativeFile = ((await import('node:' + 'buffer')) as { File: typeof File }).File
  } catch {
    nativeFile = undefined
  }
  if (!nativeFile || globalThis.File === nativeFile) {
    return fetch(url, options)
  }
  const previous = globalThis.File
  globalThis.File = nativeFile
  try {
    return await fetch(url, options)
  } finally {
    globalThis.File = previous
  }
}

/** POST /batches multipart: one 'files' part per file, 'name' only when given, 'tags' = tags.join(',')
 * only when tags non-empty. → 201 BatchWithFiles.
 *
 * The body is built by hand as bytes (instead of the global FormData): in the jsdom test
 * environment that FormData is not recognized by Node's fetch, which breaks the content-length. */
export async function uploadBatch(
  files: File[],
  name: string | null,
  tags: string[],
): Promise<BatchWithFiles> {
  const encoder = new TextEncoder()
  const chunks: Uint8Array[] = []
  for (const file of files) {
    chunks.push(...multipartFilePart(file, new Uint8Array(await file.arrayBuffer())))
  }
  if (name !== null) chunks.push(multipartField('name', name))
  if (tags.length > 0) chunks.push(multipartField('tags', tags.join(',')))
  chunks.push(encoder.encode(`--${MULTIPART_BOUNDARY}--\r\n`))

  const body = new Uint8Array(chunks.reduce((sum, chunk) => sum + chunk.byteLength, 0))
  let offset = 0
  for (const chunk of chunks) {
    body.set(chunk, offset)
    offset += chunk.byteLength
  }

  const res = await fetchMultipart(`${API_BASE}/batches`, body)
  const text = await res.text()
  const data: unknown = text ? JSON.parse(text) : undefined
  if (!res.ok) {
    const err = (data as { error?: ErrorBody } | undefined)?.error
    throw new ApiError(
      res.status,
      err ?? { code: 'INTERNAL_ERROR', message: `HTTP ${res.status}`, details: {} },
    )
  }
  return data as BatchWithFiles
}

/** GET /batches?limit=&offset= */
export function listBatches(limit = 50, offset = 0): Promise<BatchList> {
  return apiFetch<BatchList>(`/batches?limit=${limit}&offset=${offset}`)
}

export function getBatch(id: string): Promise<BatchWithFiles> {
  return apiFetch<BatchWithFiles>(`/batches/${id}`)
}

/** PATCH /batches/{id} with only the given fields. */
export function updateBatch(id: string, patch: { name?: string; tags?: string[] }): Promise<Batch> {
  return apiFetch<Batch>(`/batches/${id}`, { method: 'PATCH', body: patch })
}

/** POST /batches/{id}/ingest → 202 { items: IngestRun[] }. */
export function ingestBatch(
  id: string,
  collectionId: string,
  params: IngestParamsAll,
): Promise<{ items: IngestRun[] }> {
  return apiFetch<{ items: IngestRun[] }>(`/batches/${id}/ingest`, {
    method: 'POST',
    body: { collection_id: collectionId, params },
  })
}
