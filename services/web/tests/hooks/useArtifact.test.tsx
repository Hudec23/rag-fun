// Hook tests for src/hooks/useArtifact.ts: renderHook inside a QueryClientProvider (fresh
// client, no retries), one msw handler per test, waitFor for the async query data.
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import type { ReactNode } from 'react'

import { ApiError } from '../../src/api/client'
import { useArtifact } from '../../src/hooks/useArtifact'
import { server } from '../setup/server'

function renderArtifact(stageRunId: string | null) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return renderHook(() => useArtifact(stageRunId), {
    wrapper: ({ children }: { children?: ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    ),
  })
}

test('useArtifact("s1") fetches /api/v1/stage-runs/s1/artifact and returns data', async () => {
  const artifact = { pages: 2, tokens: 1234 }
  let calls = 0
  server.use(
    http.get('/api/v1/stage-runs/s1/artifact', () => {
      calls += 1
      return HttpResponse.json(artifact)
    }),
  )
  const { result } = renderArtifact('s1')
  await waitFor(() => expect(result.current.data).toEqual(artifact))
  expect(calls).toBe(1)
  expect(result.current.isLoading).toBe(false)
})

test('useArtifact(null) makes no request and isLoading false', () => {
  let requests = 0
  server.use(
    http.get(/stage-runs/, () => {
      requests += 1
      return HttpResponse.json({})
    }),
  )
  const { result } = renderArtifact(null)
  expect(result.current.isLoading).toBe(false)
  expect(result.current.data).toBeUndefined()
  expect(requests).toBe(0)
})

test('useArtifact: 404 ARTIFACT_NOT_FOUND → error is an ApiError', async () => {
  server.use(
    http.get('/api/v1/stage-runs/s1/artifact', () =>
      HttpResponse.json(
        {
          error: {
            code: 'ARTIFACT_NOT_FOUND',
            message: 'No artifact for this stage run',
            details: {},
          },
        },
        { status: 404 },
      ),
    ),
  )
  const { result } = renderArtifact('s1')
  await waitFor(() => expect(result.current.error).toBeInstanceOf(ApiError))
  expect((result.current.error as ApiError).status).toBe(404)
  expect((result.current.error as ApiError).code).toBe('ARTIFACT_NOT_FOUND')
  expect((result.current.error as ApiError).message).toBe('No artifact for this stage run')
})
