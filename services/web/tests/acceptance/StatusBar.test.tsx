// F-status (UI)
import { screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'

import { StatusBar } from '../../src/components/StatusBar'
import { renderWithProviders } from '../setup/render'
import { server } from '../setup/server'

test('one pill per component, failures carry their detail', async () => {
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
  expect(ollama.closest('[data-ok]')).toHaveAttribute('data-ok', 'false')
  expect(ollama.closest('[data-ok]')).toHaveAttribute('title', 'connect timeout')
  expect(screen.getByText('postgres').closest('[data-ok]')).toHaveAttribute('data-ok', 'true')
  expect(document.querySelectorAll('[data-ok]')).toHaveLength(8)
})
