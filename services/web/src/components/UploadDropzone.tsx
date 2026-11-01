export interface UploadDropzoneProps {
  onUploaded: (batchId: string) => void
}

/**
 * Drop zone + hidden <input type="file" multiple aria-label="Choose files">. Selected files listed by
 * name. Optional batch name input (label "Batch name") and <TagEditor> for batch tags. Button
 * "Upload N files" (disabled with 0 files) → uploadBatch → onUploaded(batch.id), clear selection.
 * ApiError (e.g. UNSUPPORTED_FILE_TYPE) → <ErrorBox>, selection kept.
 */
export function UploadDropzone(_props: UploadDropzoneProps): React.ReactElement {
  throw new Error('not implemented')
}
