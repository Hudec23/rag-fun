export interface CreateCollectionFormProps {
  onCreated?: () => void
}

/**
 * Inline form: name input (label "Name"), dense model select (label "Dense model", 4 options = DenseModel
 * values), sparse model select (label "Sparse model", 2 options = SparseModel values). Defaults: dense
 * "bge-m3", sparse "Qdrant/bm25". Button "Create". Submit → createCollection; success → invalidate
 * ['collections'], clear name, onCreated(); ApiError → <ErrorBox>. Button disabled while name is empty
 * or the request is pending.
 */
export function CreateCollectionForm(_props: CreateCollectionFormProps): React.ReactElement {
  throw new Error('not implemented')
}
