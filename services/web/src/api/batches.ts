import type { BatchList, BatchWithFiles, Batch, IngestParamsAll, IngestRun } from './types'

/** POST /batches multipart: one 'files' part per file, 'name' only when given, 'tags' = tags.join(',')
 * only when tags non-empty. → 201 BatchWithFiles. */
export function uploadBatch(
  _files: File[],
  _name: string | null,
  _tags: string[],
): Promise<BatchWithFiles> {
  throw new Error('not implemented')
}

/** GET /batches?limit=&offset= */
export function listBatches(_limit = 50, _offset = 0): Promise<BatchList> {
  throw new Error('not implemented')
}

export function getBatch(_id: string): Promise<BatchWithFiles> {
  throw new Error('not implemented')
}

/** PATCH /batches/{id} with only the given fields. */
export function updateBatch(
  _id: string,
  _patch: { name?: string; tags?: string[] },
): Promise<Batch> {
  throw new Error('not implemented')
}

/** POST /batches/{id}/ingest → 202 { items: IngestRun[] }. */
export function ingestBatch(
  _id: string,
  _collectionId: string,
  _params: IngestParamsAll,
): Promise<{ items: IngestRun[] }> {
  throw new Error('not implemented')
}
