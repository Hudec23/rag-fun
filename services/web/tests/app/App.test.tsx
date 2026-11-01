import { screen } from '@testing-library/react'
import { vi } from 'vitest'

import { App, NAV } from '../../src/App'
import { renderWithProviders } from '../setup/render'

// The shell must render even while pages and the status bar are still stubs.
vi.mock('../../src/components/StatusBar', () => ({ StatusBar: () => <span>status</span> }))
vi.mock('../../src/pages/FilesPage', () => ({ FilesPage: () => <p>files page</p> }))

test('renders navigation with every page link', () => {
  renderWithProviders(<App />)
  for (const n of NAV) expect(screen.getByRole('link', { name: n.label })).toBeInTheDocument()
})

test('root route shows the files page', () => {
  renderWithProviders(<App />, { path: '/' })
  expect(screen.getByText('files page')).toBeInTheDocument()
})
