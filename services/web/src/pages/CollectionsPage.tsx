import { useCollections } from '../hooks/useCollections'
import { ErrorBox } from '../components/ErrorBox'
import { CreateCollectionForm } from '../components/CreateCollectionForm'

/** Example page (house style): data via a react-query hook, loading + error states, Tailwind only. */
export function CollectionsPage() {
  const { data, error, isLoading } = useCollections()
  if (isLoading) return <p className="p-4 text-sm text-gray-500">Loading…</p>
  if (error) return <ErrorBox error={error} />
  return (
    <section className="p-4">
      <h1 className="mb-3 text-lg font-semibold">Collections</h1>
      <ul className="divide-y rounded border bg-white">
        {data!.items.map((c) => (
          <li key={c.id} className="flex justify-between p-3">
            <span className="font-medium">{c.name}</span>
            <span className="text-sm text-gray-500">
              {c.dense_model} · {c.dense_dims}d · {c.sparse_model}
            </span>
          </li>
        ))}
      </ul>
      <CreateCollectionForm />
    </section>
  )
}
