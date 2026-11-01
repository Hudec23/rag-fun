import type { ErrorBody } from './types'

export const API_BASE: string = import.meta.env.VITE_API_BASE ?? '/api/v1'

/** Thrown for every non-2xx response; carries the contract error body. */
export class ApiError extends Error {
  status: number
  code: string
  details: Record<string, unknown>

  constructor(status: number, body: ErrorBody) {
    super(body.message)
    this.status = status
    this.code = body.code
    this.details = body.details
  }
}

/** fetch JSON from the api. Non-2xx → ApiError (code INTERNAL_ERROR when the body is not the
 * contract shape). 204 → undefined. Body objects are sent as JSON; FormData as-is. */
export async function apiFetch<T>(
  path: string,
  init: Omit<RequestInit, 'body'> & { body?: unknown } = {},
): Promise<T> {
  const { body, headers, ...rest } = init
  const isForm = body instanceof FormData
  const res = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers:
      isForm || body === undefined ? headers : { 'Content-Type': 'application/json', ...headers },
    body: body === undefined ? undefined : isForm ? (body as FormData) : JSON.stringify(body),
  })
  if (res.status === 204) return undefined as T
  const text = await res.text()
  const data: unknown = text ? JSON.parse(text) : undefined
  if (!res.ok) {
    const err = (data as { error?: ErrorBody } | undefined)?.error
    throw new ApiError(
      res.status,
      err ?? { code: 'INTERNAL_ERROR', message: `HTTP ${res.status}`, details: {} },
    )
  }
  return data as T
}
