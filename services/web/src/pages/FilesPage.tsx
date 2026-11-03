/**
 * Route "/". <UploadDropzone> on top; then batches (listBatches) each with its files table: filename,
 * type, size (KB/MB, 1 decimal), tags (<TagEditor> → updateFileTags), actions "Ingest…" (collection
 * select + "Start" → createIngestRun then navigate to /ingest/<runId>) and "Delete" (confirm →
 * deleteFile). Batch row: name, tags editor (updateBatch), "Ingest batch" (collection select → ingestBatch
 * with INGEST_DEFAULTS, then shows "<n> runs started" with links).
 */
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router'

import { getBatch, ingestBatch, listBatches, updateBatch } from '../api/batches'
import { deleteFile, updateFileTags } from '../api/files'
import { createIngestRun } from '../api/runs'
import type { Batch, Collection, FileItem, IngestRun } from '../api/types'
import { ErrorBox } from '../components/ErrorBox'
import { TagEditor } from '../components/TagEditor'
import { UploadDropzone } from '../components/UploadDropzone'
import { useCollections } from '../hooks/useCollections'
import { INGEST_DEFAULTS } from '../lib/defaults'

const CONTROL_CLASS = 'rounded border border-gray-300 bg-white px-2 py-1 text-sm'

/** Bytes → KB/MB with 1 decimal (482113 → "470.8 KB", 512 → "0.5 KB", 3·1024² → "3.0 MB"). */
function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function CollectionSelect({
  value,
  collections,
  onChange,
}: {
  value: string
  collections: Collection[]
  onChange: (id: string) => void
}): React.ReactElement {
  return (
    <select
      aria-label="Collection"
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className={CONTROL_CLASS}
    >
      <option value="">Collection…</option>
      {collections.map((collection) => (
        <option key={collection.id} value={collection.id}>
          {collection.name}
        </option>
      ))}
    </select>
  )
}

function FileRow({
  file,
  collections,
}: {
  file: FileItem
  collections: Collection[]
}): React.ReactElement {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [tags, setTags] = useState<string[]>(file.tags)
  const [error, setError] = useState<unknown>(null)
  const [ingestOpen, setIngestOpen] = useState(false)
  const [collectionId, setCollectionId] = useState('')
  const [starting, setStarting] = useState(false)

  const saveTags = (next: string[]) => {
    setTags(next)
    updateFileTags(file.id, next).catch((err) => setError(err))
  }

  const startIngest = async () => {
    if (collectionId === '' || starting) return
    setError(null)
    setStarting(true)
    try {
      const run = await createIngestRun(file.id, collectionId)
      navigate(`/ingest/${run.id}`)
    } catch (err) {
      setError(err)
      setStarting(false)
    }
  }

  const remove = async () => {
    if (!window.confirm(`Delete ${file.filename}?`)) return
    setError(null)
    try {
      await deleteFile(file.id)
      void queryClient.invalidateQueries({ queryKey: ['batch', file.batch_id] })
    } catch (err) {
      setError(err)
    }
  }

  return (
    <tr className="border-b border-gray-100 align-top">
      <td className="p-2">{file.filename}</td>
      <td className="p-2 text-gray-500">{file.mime}</td>
      <td className="p-2 text-gray-500">{formatSize(file.size_bytes)}</td>
      <td className="p-2">
        <TagEditor tags={tags} onChange={saveTags} />
      </td>
      <td className="p-2">
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setIngestOpen(!ingestOpen)}
            className={CONTROL_CLASS}
          >
            Ingest…
          </button>
          {ingestOpen ? (
            <>
              <CollectionSelect
                value={collectionId}
                collections={collections}
                onChange={setCollectionId}
              />
              <button
                type="button"
                disabled={collectionId === '' || starting}
                onClick={() => void startIngest()}
                className={CONTROL_CLASS}
              >
                Start
              </button>
            </>
          ) : null}
          <button type="button" onClick={() => void remove()} className={CONTROL_CLASS}>
            Delete
          </button>
        </div>
        {error !== null ? <ErrorBox error={error} /> : null}
      </td>
    </tr>
  )
}

function BatchCard({
  batch,
  collections,
}: {
  batch: Batch
  collections: Collection[]
}): React.ReactElement {
  const detail = useQuery({
    queryKey: ['batch', batch.id],
    queryFn: () => getBatch(batch.id),
  })
  const [tags, setTags] = useState<string[]>(batch.tags)
  const [tagsError, setTagsError] = useState<unknown>(null)
  const [ingestOpen, setIngestOpen] = useState(false)
  const [collectionId, setCollectionId] = useState('')
  const [runs, setRuns] = useState<IngestRun[]>([])
  const [ingestError, setIngestError] = useState<unknown>(null)
  const [starting, setStarting] = useState(false)

  const saveTags = (next: string[]) => {
    setTags(next)
    updateBatch(batch.id, { tags: next }).catch((err) => setTagsError(err))
  }

  const startIngest = async (id: string) => {
    setCollectionId(id)
    if (id === '' || starting) return
    setIngestError(null)
    setStarting(true)
    try {
      const result = await ingestBatch(batch.id, id, INGEST_DEFAULTS)
      setRuns(result.items)
    } catch (err) {
      setIngestError(err)
    } finally {
      setStarting(false)
    }
  }

  return (
    <article className="space-y-3 rounded border bg-white p-4">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-base font-semibold">{batch.name}</h2>
        <TagEditor tags={tags} onChange={saveTags} />
        <button type="button" onClick={() => setIngestOpen(!ingestOpen)} className={CONTROL_CLASS}>
          Ingest batch
        </button>
      </div>
      {tagsError !== null ? <ErrorBox error={tagsError} /> : null}
      {ingestOpen ? (
        <div className="flex flex-wrap items-center gap-3">
          <CollectionSelect
            value={collectionId}
            collections={collections}
            onChange={(id) => void startIngest(id)}
          />
          {runs.length > 0 ? (
            <div className="space-y-1">
              <p className="text-sm text-gray-500">
                {runs.length === 1 ? '1 run started' : `${runs.length} runs started`}
              </p>
              <ul className="flex flex-wrap gap-3">
                {runs.map((run) => (
                  <li key={run.id} className="text-sm">
                    <a className="text-blue-700 underline" href={`/ingest/${run.id}`}>
                      {run.id}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
      {ingestError !== null ? <ErrorBox error={ingestError} /> : null}
      {detail.isLoading ? (
        <p className="p-2 text-sm text-gray-500">Loading…</p>
      ) : detail.error ? (
        <ErrorBox error={detail.error} />
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-left text-xs uppercase text-gray-500">
              <th className="p-2 font-medium">Filename</th>
              <th className="p-2 font-medium">Type</th>
              <th className="p-2 font-medium">Size</th>
              <th className="p-2 font-medium">Tags</th>
              <th className="p-2 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {detail.data!.files.map((file) => (
              <FileRow key={file.id} file={file} collections={collections} />
            ))}
          </tbody>
        </table>
      )}
    </article>
  )
}

export function FilesPage(): React.ReactElement {
  const queryClient = useQueryClient()
  const collections = useCollections()
  const batches = useQuery({
    queryKey: ['batches'],
    queryFn: () => listBatches(),
  })
  const items = collections.data?.items ?? []

  const onUploaded = () => {
    void queryClient.invalidateQueries({ queryKey: ['batches'] })
    void queryClient.invalidateQueries({ queryKey: ['batch'] })
  }

  return (
    <section className="space-y-4 p-4">
      <h1 className="text-lg font-semibold">Files</h1>
      <UploadDropzone onUploaded={onUploaded} />
      {batches.isLoading ? (
        <p className="text-sm text-gray-500">Loading…</p>
      ) : batches.error ? (
        <ErrorBox error={batches.error} />
      ) : batches.data!.items.length === 0 ? (
        <p className="text-sm text-gray-500">No batches yet — upload files above.</p>
      ) : (
        batches.data!.items.map((batch) => (
          <BatchCard key={batch.id} batch={batch} collections={items} />
        ))
      )}
    </section>
  )
}
