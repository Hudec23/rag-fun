import type { StageRun } from '../api/types'

export interface StageStepperProps {
  stages: { name: string; run: StageRun | null }[]
  selected: string
  onSelect: (stage: string) => void
}

/**
 * Horizontal steps in the given order. Each step is a button with the stage name and a status badge:
 * "not run" when run is null, else run.status (+ " v<version>"). Badge colors: done green, failed red,
 * running/queued blue (with animate-pulse), stale amber. aria-current="step" on the selected one.
 */
export function StageStepper(_props: StageStepperProps): React.ReactElement {
  throw new Error('not implemented')
}
