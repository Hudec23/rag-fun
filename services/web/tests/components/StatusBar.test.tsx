// StatusBar (F-status): "Checking services…" while loading, one pill per component in response
// order (data-ok attribute, red pill title = detail), one red "api" pill on request error,
// react-query polling with refetchInterval 5000.
import { act } from 'react'
import { screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { vi } from 'vitest'

import { StatusBar } from '../../src/components/StatusBar'
import { renderWithProviders } from '../setup/render'
import { server } from '../setup/server'

test('while loading: shows "Checking services…" until the request resolves', async () => {
  server.use(http.get('/api/v1/status', () => new Promise<never>(() => {})))
  renderWithProviders(<StatusBar />)
  expect(await screen.findByText('Checking services…')).toBeInTheDocument()
})

test('8 components: 8 elements with data-ok in response order, red one has title = detail', async () => {
  const names = [
    'api',
    'worker-ingest',
    'worker-query',
    'postgres',
    'redis',
    'qdrant',
    's3',
    'ollama',
  ]
  server.use(
    http.get('/api/v1/status', () =>
      HttpResponse.json({
        components: names.map((name) => ({
          name,
          ok: name !== 'ollama',
          latency_ms: 1,
          detail: name === 'ollama' ? 'connect timeout' : null,
        })),
      }),
    ),
  )
  renderWithProviders(<StatusBar />)
  const ollama = await screen.findByText('ollama')
  const pills = Array.from(document.querySelectorAll('[data-ok]'))
  expect(pills).toHaveLength(8)
  expect(pills.map((pill) => pill.textContent)).toEqual(names)
  expect(ollama.closest('[data-ok]')).toHaveAttribute('data-ok', 'false')
  expect(ollama.closest('[data-ok]')).toHaveAttribute('title', 'connect timeout')
  expect(screen.getByText('postgres').closest('[data-ok]')).toHaveAttribute('data-ok', 'true')
})

test('GET /status 500: one red "api" pill with data-ok false', async () => {
  server.use(
    http.get('/api/v1/status', () =>
      HttpResponse.json(
        {
          error: {
            code: 'INTERNAL_ERROR',
            message: 'internal error',
            details: {},
          },
        },
        { status: 500 },
      ),
    ),
  )
  renderWithProviders(<StatusBar />)
  const api = await screen.findByText('api')
  expect(api.closest('[data-ok]')).toHaveAttribute('data-ok', 'false')
  expect(document.querySelectorAll('[data-ok]')).toHaveLength(1)
})

test('refetchInterval: uses react-query with refetchInterval 5000 (2 requests after 5 s)', async () => {
  let requests = 0
  server.use(
    http.get('/api/v1/status', () => {
      requests += 1
      return HttpResponse.json({
        components: [{ name: 'api', ok: true, latency_ms: 1, detail: null }],
      })
    }),
  )
  vi.useFakeTimers()
  try {
    renderWithProviders(<StatusBar />)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000)
    })
    expect(requests).toBe(2)
  } finally {
    vi.useRealTimers()
  }
})
