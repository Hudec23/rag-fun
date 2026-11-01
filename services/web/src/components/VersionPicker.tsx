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
export function VersionPicker(_props: VersionPickerProps): React.ReactElement {
  throw new Error('not implemented')
}
