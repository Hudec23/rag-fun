export interface ProgressBarProps {
  done: number
  total: number
  message?: string
}

/**
 * role="progressbar" with aria-valuenow=done, aria-valuemax=total, width % = round(done/total*100)
 * (0 when total ≤ 0, max 100). Shows "<done>/<total>" and message when given.
 */
export function ProgressBar(_props: ProgressBarProps): React.ReactElement {
  throw new Error('not implemented')
}
