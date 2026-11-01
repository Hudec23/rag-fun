import type { RunEvent } from '../api/types'

/** Opens EventSource(`${API_BASE}/events?run_id=${runId}`) while runId is non-null; for each of the
 * 6 event types (addEventListener per type) parses event.data as JSON and calls onEvent.
 * Closes on unmount or runId change. Malformed JSON is ignored. */
export function useRunEvents(_runId: string | null, _onEvent: (e: RunEvent) => void): void {
  throw new Error('not implemented')
}
