import type { PayloadFilter } from '../api/types'

export interface FilterBuilderProps {
  collectionId: string
  value: PayloadFilter
  onChange: (f: PayloadFilter) => void
}

/**
 * Edits value.must only. Rows: key select (aria-label "key"; file_id, batch_id, tags, mime, element_type,
 * chunk_strategy, parse_strategy, page, chunk_index). Keyword keys → "is any of" with
 * <select multiple aria-label="values"> whose options (value = facet value, text "value (count)") come
 * from getFacet(collectionId, key); page/chunk_index → "between" with two number inputs (aria-labels
 * "from", "to"; empty = omitted). "Add condition" button appends {key: 'tags', match: {any: []}} (not
 * emitted until it has ≥1 value); "×" (aria-label "remove condition") removes a row. Emits only
 * complete conditions.
 */
export function FilterBuilder(_props: FilterBuilderProps): React.ReactElement {
  throw new Error('not implemented')
}
