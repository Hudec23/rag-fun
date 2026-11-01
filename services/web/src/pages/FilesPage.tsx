/**
 * Route "/". <UploadDropzone> on top; then batches (listBatches) each with its files table: filename,
 * type, size (KB/MB, 1 decimal), tags (<TagEditor> → updateFileTags), actions "Ingest…" (collection
 * select + "Start" → createIngestRun then navigate to /ingest/<runId>) and "Delete" (confirm →
 * deleteFile). Batch row: name, tags editor (updateBatch), "Ingest batch" (collection select → ingestBatch
 * with INGEST_DEFAULTS, then shows "<n> runs started" with links).
 */
export function FilesPage(): React.ReactElement {
  throw new Error('not implemented')
}
