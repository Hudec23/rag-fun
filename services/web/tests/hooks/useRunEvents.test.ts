// Hook tests for src/hooks/useRunEvents.ts: MockEventSource replaces the global EventSource
// (tests/setup/setup.ts), renderHook drives the hook and MockEventSource.last().emit(type, data)
// delivers SSE events. Instances are reset after every test.
import { renderHook } from '@testing-library/react'
import { vi } from 'vitest'

import type { RunEvent } from '../../src/api/types'
import { useRunEvents } from '../../src/hooks/useRunEvents'
import { RUN_ID } from '../setup/fixtures'
import { MockEventSource } from '../setup/eventsource'

const STAGE_RUN_ID = '019a4b2c-2101-7c00-9000-000000000003'
const TS = '2026-11-01T18:22:05.123Z'

const STARTED: RunEvent = {
  type: 'stage.started',
  run_id: RUN_ID,
  stage_run_id: STAGE_RUN_ID,
  stage: 'parse',
  version: 1,
  ts: TS,
}
const PROGRESS: RunEvent = {
  type: 'stage.progress',
  run_id: RUN_ID,
  stage_run_id: STAGE_RUN_ID,
  stage: 'parse',
  version: 1,
  ts: TS,
  done: 3,
  total: 8,
  message: 'parsing 3/8 pages',
}
const COMPLETED: RunEvent = {
  type: 'stage.completed',
  run_id: RUN_ID,
  stage_run_id: STAGE_RUN_ID,
  stage: 'parse',
  version: 1,
  ts: TS,
  artifact_key: `${RUN_ID}/parse/v1.json`,
  summary: { pages: 8 },
}
const FAILED: RunEvent = {
  type: 'stage.failed',
  run_id: RUN_ID,
  stage_run_id: STAGE_RUN_ID,
  stage: 'parse',
  version: 1,
  ts: TS,
  error: { code: 'PARSE_FAILED', message: 'Could not parse the file', details: {} },
}
const TOKEN: RunEvent = {
  type: 'generate.token',
  run_id: RUN_ID,
  stage_run_id: STAGE_RUN_ID,
  stage: 'generate',
  version: 1,
  ts: TS,
  index: 2,
  text: 'hello',
}
const UPDATED: RunEvent = {
  type: 'run.updated',
  run_id: RUN_ID,
  run_kind: 'ingest',
  reason: 'stage completed',
  ts: TS,
}
const EVENTS: RunEvent[] = [STARTED, PROGRESS, COMPLETED, FAILED, TOKEN, UPDATED]

function renderEvents(onEvent: (e: RunEvent) => void, runId: string | null = 'r1') {
  return renderHook(() => useRunEvents(runId, onEvent))
}

test('opens one event source with the run id', () => {
  renderEvents(vi.fn())
  expect(MockEventSource.instances).toHaveLength(1)
  expect(MockEventSource.instances[0].url).toBe('/api/v1/events?run_id=r1')
})

test('calls onEvent once with the parsed event data', () => {
  const onEvent = vi.fn()
  renderEvents(onEvent)
  MockEventSource.last().emit('stage.progress', PROGRESS)
  expect(onEvent).toHaveBeenCalledTimes(1)
  expect(onEvent).toHaveBeenCalledWith(PROGRESS)
})

test('delivers each of the six event types', () => {
  const onEvent = vi.fn()
  renderEvents(onEvent)
  const source = MockEventSource.last()
  for (const event of EVENTS) source.emit(event.type, event)
  expect(onEvent).toHaveBeenCalledTimes(EVENTS.length)
  for (let i = 0; i < EVENTS.length; i++) expect(onEvent).toHaveBeenNthCalledWith(i + 1, EVENTS[i])
})

test('ignores malformed json data', () => {
  const onEvent = vi.fn()
  renderEvents(onEvent)
  expect(() => MockEventSource.last().emit('stage.started', '{not valid json')).not.toThrow()
  expect(onEvent).not.toHaveBeenCalled()
})

test('closes the source on unmount and creates none when the run id is null', () => {
  const onEvent = vi.fn()
  const { unmount } = renderEvents(onEvent)
  unmount()
  expect(MockEventSource.instances).toHaveLength(1)
  expect(MockEventSource.instances[0].closed).toBe(true)

  renderEvents(onEvent, null)
  expect(MockEventSource.instances).toHaveLength(1)
})

test('closes the old source and opens a new one when the run id changes', () => {
  const onEvent = vi.fn()
  const { rerender } = renderHook(({ runId }: { runId: string }) => useRunEvents(runId, onEvent), {
    initialProps: { runId: 'r1' },
  })
  rerender({ runId: 'r2' })
  expect(MockEventSource.instances).toHaveLength(2)
  expect(MockEventSource.instances[0].url).toBe('/api/v1/events?run_id=r1')
  expect(MockEventSource.instances[0].closed).toBe(true)
  expect(MockEventSource.instances[1].url).toBe('/api/v1/events?run_id=r2')
  expect(MockEventSource.instances[1].closed).toBe(false)
})
