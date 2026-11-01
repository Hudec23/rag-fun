import { setupServer } from 'msw/node'

/** msw server; tests add handlers with server.use(http.get('/api/v1/...', ...)). Unhandled → error. */
export const server = setupServer()
