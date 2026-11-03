import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { createCollection } from '../api/collections'
import { collectionsKey } from '../hooks/useCollections'
import type { CollectionCreate } from '../api/types'
import { ErrorBox } from './ErrorBox'

type DenseModel = CollectionCreate['dense_model']
type SparseModel = CollectionCreate['sparse_model']

const DENSE_MODELS: readonly DenseModel[] = [
  'bge-m3',
  'nomic-embed-text',
  'mxbai-embed-large',
  'all-minilm',
]
const SPARSE_MODELS: readonly SparseModel[] = ['Qdrant/bm25', 'prithivida/Splade_PP_en_v1']

const ROW_CLASS = 'flex items-center gap-2 text-sm'
const NAME_CLASS = 'w-24 text-gray-700'
const CONTROL_CLASS = 'rounded border border-gray-300 bg-white px-2 py-1 text-sm'

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
export function CreateCollectionForm({ onCreated }: CreateCollectionFormProps): React.ReactElement {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [denseModel, setDenseModel] = useState<DenseModel>('bge-m3')
  const [sparseModel, setSparseModel] = useState<SparseModel>('Qdrant/bm25')
  const [error, setError] = useState<unknown>(null)

  const mutation = useMutation({
    mutationFn: (body: CollectionCreate) => createCollection(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: collectionsKey })
      setName('')
      setError(null)
      onCreated?.()
    },
    onError: (err) => {
      setError(err)
    },
  })

  const canSubmit = name !== '' && !mutation.isPending

  const submit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!canSubmit) return
    setError(null)
    mutation.mutate({ name, dense_model: denseModel, sparse_model: sparseModel })
  }

  return (
    <form className="mt-3 space-y-2" onSubmit={submit}>
      <div className="flex flex-wrap items-center gap-3">
        <label className={ROW_CLASS}>
          <span className={NAME_CLASS}>Name</span>
          <input
            type="text"
            className={CONTROL_CLASS}
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </label>
        <label className={ROW_CLASS}>
          <span className={NAME_CLASS}>Dense model</span>
          <select
            className={CONTROL_CLASS}
            value={denseModel}
            onChange={(event) => setDenseModel(event.target.value as DenseModel)}
          >
            {DENSE_MODELS.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </label>
        <label className={ROW_CLASS}>
          <span className={NAME_CLASS}>Sparse model</span>
          <select
            className={CONTROL_CLASS}
            value={sparseModel}
            onChange={(event) => setSparseModel(event.target.value as SparseModel)}
          >
            {SPARSE_MODELS.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" disabled={!canSubmit} className={CONTROL_CLASS}>
          Create
        </button>
      </div>
      {error !== null ? <ErrorBox error={error} /> : null}
    </form>
  )
}
