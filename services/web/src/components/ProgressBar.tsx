export interface ProgressBarProps {
  done: number
  total: number
  message?: string
}

/**
 * role="progressbar" with aria-valuenow=done, aria-valuemax=total, width % = round(done/total*100)
 * (0 when total ≤ 0, max 100). Shows "<done>/<total>" and message when given.
 */
export function ProgressBar({ done, total, message }: ProgressBarProps): React.ReactElement {
  const pct = total > 0 ? Math.min(100, Math.round((done / total) * 100)) : 0
  return (
    <div className="w-full">
      <div className="mb-1 flex items-center justify-between text-xs text-gray-500">
        <span>
          {done}/{total}
        </span>
        {message ? <span>{message}</span> : null}
      </div>
      <div className="h-2 w-full overflow-hidden rounded bg-gray-200">
        <div
          role="progressbar"
          aria-valuenow={done}
          aria-valuemax={total}
          className="h-full bg-blue-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
