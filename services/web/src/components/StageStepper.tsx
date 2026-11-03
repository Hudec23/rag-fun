import type { StageRun } from '../api/types'

export interface StageStepperProps {
  stages: { name: string; run: StageRun | null }[]
  selected: string
  onSelect: (stage: string) => void
}

const BADGE_CLASS: Record<StageRun['status'], string> = {
  done: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  running: 'animate-pulse bg-blue-100 text-blue-800',
  queued: 'animate-pulse bg-blue-100 text-blue-800',
  stale: 'bg-amber-100 text-amber-800',
}

/**
 * Horizontal steps in the given order. Each step is a button with the stage name and a status badge:
 * "not run" when run is null, else run.status (+ " v<version>"). Badge colors: done green, failed red,
 * running/queued blue (with animate-pulse), stale amber. aria-current="step" on the selected one.
 */
export function StageStepper({
  stages,
  selected,
  onSelect,
}: StageStepperProps): React.ReactElement {
  return (
    <nav aria-label="Stages" className="flex flex-wrap items-center gap-2">
      {stages.map(({ name, run }) => {
        const isSelected = selected === name
        return (
          <button
            key={name}
            type="button"
            aria-current={isSelected ? 'step' : undefined}
            onClick={() => onSelect(name)}
            className={`flex items-center gap-2 rounded border px-3 py-1.5 text-sm ${
              isSelected ? 'border-blue-500' : 'border-gray-300'
            }`}
          >
            <span className="font-medium">{name}</span>
            <Badge run={run} />
          </button>
        )
      })}
    </nav>
  )
}

function Badge({ run }: { run: StageRun | null }) {
  const classes = run
    ? `${BADGE_CLASS[run.status]} rounded-full px-2 py-0.5 text-xs`
    : 'rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500'
  const label = run ? `${run.status} v${run.version}` : 'not run'
  return <span className={classes}>{label}</span>
}
