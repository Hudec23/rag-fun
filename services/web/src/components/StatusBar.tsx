import { useQuery } from '@tanstack/react-query'

import { ApiError } from '../api/client'
import { getStatus } from '../api/system'

/**
 * Polls getStatus every 5 s (react-query refetchInterval). Renders one pill per component in response
 * order: text = component name, data-ok="true|false", green when ok, red when not with title = detail.
 * While loading: "Checking services…". Request error: one red pill "api" with the error message.
 */
export function StatusBar(): React.ReactElement {
  const { data, error, isLoading } = useQuery({
    queryKey: ['status'],
    queryFn: getStatus,
    refetchInterval: 5000,
  })
  if (isLoading) return <p className="p-4 text-sm text-gray-500">Checking services…</p>
  if (error || !data) {
    return (
      <div className="flex flex-wrap gap-1 p-4">
        <Pill name="api" ok={false} title={describeError(error)} />
      </div>
    )
  }
  return (
    <div className="flex flex-wrap gap-1 p-4">
      {data.components.map((c) => (
        <Pill key={c.name} name={c.name} ok={c.ok} title={c.detail ?? undefined} />
      ))}
    </div>
  )
}

function Pill({
  name,
  ok,
  title,
}: {
  name: string
  ok: boolean
  title?: string
}): React.ReactElement {
  return (
    <span
      data-ok={ok ? 'true' : 'false'}
      title={title}
      className={`rounded-full px-2 py-0.5 text-xs font-medium text-white ${
        ok ? 'bg-green-500' : 'bg-red-500'
      }`}
    >
      {name}
    </span>
  )
}

function describeError(error: unknown): string {
  if (error instanceof ApiError) return `${error.code}: ${error.message}`
  if (error instanceof Error) return error.message
  return String(error)
}
