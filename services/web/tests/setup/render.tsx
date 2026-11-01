import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import type { ReactElement } from 'react'
import { MemoryRouter, Route, Routes } from 'react-router'

/** Render inside a fresh QueryClient (no retries) and a MemoryRouter at `path`.
 * `route` = the route pattern when the component reads params (e.g. '/ingest/:runId'). */
export function renderWithProviders(
  ui: ReactElement,
  opts: { path?: string; route?: string } = {},
) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const path = opts.path ?? '/'
  return {
    client,
    ...render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={[path]}>
          {opts.route ? (
            <Routes>
              <Route path={opts.route} element={ui} />
            </Routes>
          ) : (
            ui
          )}
        </MemoryRouter>
      </QueryClientProvider>,
    ),
  }
}
