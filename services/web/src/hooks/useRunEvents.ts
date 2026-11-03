import { useEffect, useRef } from 'react'

import { API_BASE } from '../api/client'
import type { RunEvent } from '../api/types'

/** The 6 SSE event types (contracts/events/*.schema.json). */
const RUN_EVENT_TYPES: readonly RunEvent['type'][] = [
  'stage.started',
  'stage.progress',
  'stage.completed',
  'stage.failed',
  'generate.token',
  'run.updated',
]

/** Opens EventSource(`${API_BASE}/events?run_id=${runId}`) while runId is non-null; for each of the
 * 6 event types (addEventListener per type) parses event.data as JSON and calls onEvent.
 * Closes on unmount or runId change. Malformed JSON is ignored. */
export function useRunEvents(runId: string | null, onEvent: (e: RunEvent) => void): void {
  const onEventRef = useRef(onEvent)
  useEffect(() => {
    onEventRef.current = onEvent
  }, [onEvent])

  useEffect(() => {
    if (runId === null) return

    const source = new EventSource(`${API_BASE}/events?run_id=${runId}`)
    for (const type of RUN_EVENT_TYPES) {
      source.addEventListener(type, (e: MessageEvent) => {
        try {
          onEventRef.current(JSON.parse(e.data) as RunEvent)
        } catch {
          // ignore malformed JSON
        }
      })
    }
    return () => source.close()
  }, [runId])
}
