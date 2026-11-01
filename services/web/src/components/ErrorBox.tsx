import { ApiError } from '../api/client'

/** Shows an error: ApiError → "<code>: <message>"; anything else → its message. */
export function ErrorBox({ error }: { error: unknown }) {
  const text =
    error instanceof ApiError
      ? `${error.code}: ${error.message}`
      : error instanceof Error
        ? error.message
        : String(error)
  return (
    <div
      role="alert"
      className="m-2 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800"
    >
      {text}
    </div>
  )
}
