import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterAll, afterEach, beforeAll, vi } from 'vitest'

import { MockEventSource } from './eventsource'
import { server } from './server'

// Plotly needs WebGL/canvas: replace <Plot> with a div exposing its figure as JSON.
vi.mock('react-plotly.js', async () => {
  const { createElement } = await import('react')
  return {
    default: (props: { data: unknown; layout?: unknown }) =>
      createElement('div', {
        'data-testid': 'plot',
        'data-figure': JSON.stringify({ data: props.data, layout: props.layout ?? {} }),
      }),
  }
})

// React Flow measures DOM nodes.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver
globalThis.EventSource = MockEventSource as unknown as typeof EventSource

beforeAll(() => server.listen({ onUnhandledFrame: 'error' }))
afterEach(() => {
  cleanup()
  server.resetHandlers()
  MockEventSource.reset()
})
afterAll(() => server.close())
