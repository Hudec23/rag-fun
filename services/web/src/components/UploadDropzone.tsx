import { useState } from 'react'

import { uploadBatch } from '../api/batches'
import { ErrorBox } from './ErrorBox'
import { TagEditor } from './TagEditor'

const ROW_CLASS = 'flex items-center gap-2 text-sm'
const NAME_CLASS = 'w-24 text-gray-700'
const CONTROL_CLASS = 'rounded border border-gray-300 bg-white px-2 py-1 text-sm'

export interface UploadDropzoneProps {
  onUploaded: (batchId: string) => void
}

/**
 * Drop zone + hidden <input type="file" multiple aria-label="Choose files">. Selected files listed by
 * name. Optional batch name input (label "Batch name") and <TagEditor> for batch tags. Button
 * "Upload N files" (disabled with 0 files) → uploadBatch → onUploaded(batch.id), clear selection.
 * ApiError (e.g. UNSUPPORTED_FILE_TYPE) → <ErrorBox>, selection kept.
 */
export function UploadDropzone({ onUploaded }: UploadDropzoneProps): React.ReactElement {
  const [files, setFiles] = useState<File[]>([])
  const [name, setName] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [error, setError] = useState<unknown>(null)
  const [uploading, setUploading] = useState(false)

  const selectFiles = (list: FileList | null) => {
    if (list !== null) setFiles(Array.from(list))
  }

  const upload = async () => {
    if (files.length === 0 || uploading) return
    setError(null)
    setUploading(true)
    try {
      const result = await uploadBatch(files, name === '' ? null : name, tags)
      setFiles([])
      setName('')
      setTags([])
      onUploaded(result.batch.id)
    } catch (err) {
      setError(err)
    } finally {
      setUploading(false)
    }
  }

  return (
    <section className="space-y-2 p-4">
      <div
        className="rounded border border-dashed border-gray-400 p-4 text-sm text-gray-500"
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault()
          selectFiles(event.dataTransfer.files)
        }}
      >
        Drop files here
        <input
          type="file"
          multiple
          aria-label="Choose files"
          className="hidden"
          onChange={(event) => selectFiles(event.target.files)}
        />
      </div>
      {files.length > 0 ? (
        <ul className="divide-y rounded border bg-white">
          {files.map((file, index) => (
            <li key={index} className="p-3 text-sm">
              {file.name}
            </li>
          ))}
        </ul>
      ) : null}
      <label className={ROW_CLASS}>
        <span className={NAME_CLASS}>Batch name</span>
        <input
          type="text"
          className={CONTROL_CLASS}
          value={name}
          onChange={(event) => setName(event.target.value)}
        />
      </label>
      <TagEditor tags={tags} onChange={setTags} />
      <button
        type="button"
        disabled={files.length === 0 || uploading}
        onClick={() => void upload()}
        className={CONTROL_CLASS}
      >
        Upload {files.length} files
      </button>
      {error !== null ? <ErrorBox error={error} /> : null}
    </section>
  )
}
