import { useQuery } from '@tanstack/react-query'

import { listStageRuns } from '../api/runs'
import type { Stage } from '../api/types'

export interface VersionPickerProps {
  runId: string
  stage: Stage
  selectedId: string | null
  onSelect: (stageRunId: string) => void
}

/**
 * <select aria-label="Version"> listing listStageRuns(runId, stage) items as "v<version> · <status>",
 * newest first; value = selectedId; change → onSelect(id). Hidden when there are < 2 versions.
 */
export function VersionPicker({
  runId,
  stage,
  selectedId,
  onSelect,
}: VersionPickerProps): React.ReactElement {
  const { data, isPending } = useQuery({
    queryKey: ['stage-runs', runId, stage],
    queryFn: () => listStageRuns(runId, stage),
  })
  const items = [...(data?.items ?? [])].sort((a, b) => b.version - a.version)
  if (isPending || items.length < 2) return <></>
  return (
    <select
      aria-label="Version"
      className="rounded border border-gray-300 bg-white px-2 py-1 text-sm"
      value={selectedId ?? ''}
      onChange={(event) => onSelect(event.target.value)}
    >
      {items.map((item) => (
        <option key={item.id} value={item.id}>
          {`v${item.version} · ${item.status}`}
        </option>
      ))}
    </select>
  )
}
