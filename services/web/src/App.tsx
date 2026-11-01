import { NavLink, Route, Routes } from 'react-router'

import { StatusBar } from './components/StatusBar'
import { CollectionsPage } from './pages/CollectionsPage'
import { FilesPage } from './pages/FilesPage'
import { IngestRunPage } from './pages/IngestRunPage'
import { PipelinesPage } from './pages/PipelinesPage'
import { QdrantBrowserPage } from './pages/QdrantBrowserPage'
import { QueryPage } from './pages/QueryPage'
import { SettingsPage } from './pages/SettingsPage'

export const NAV = [
  { to: '/', label: 'Files' },
  { to: '/collections', label: 'Collections' },
  { to: '/query', label: 'Ask' },
  { to: '/qdrant', label: 'Qdrant' },
  { to: '/pipelines', label: 'Pipelines' },
  { to: '/settings', label: 'Settings' },
]

export function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center gap-4 border-b bg-white px-4 py-2">
        <span className="font-bold">rag-fun</span>
        <nav className="flex gap-3 text-sm">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === '/'}
              className={({ isActive }) =>
                isActive ? 'font-semibold text-blue-700' : 'text-gray-600'
              }
            >
              {n.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<FilesPage />} />
          <Route path="/collections" element={<CollectionsPage />} />
          <Route path="/ingest/:runId" element={<IngestRunPage />} />
          <Route path="/query" element={<QueryPage />} />
          <Route path="/query/:runId" element={<QueryPage />} />
          <Route path="/qdrant/:collectionId?" element={<QdrantBrowserPage />} />
          <Route path="/pipelines" element={<PipelinesPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
      <footer className="border-t bg-white px-4 py-1">
        <StatusBar />
      </footer>
    </div>
  )
}
