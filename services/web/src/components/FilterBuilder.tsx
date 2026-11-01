import type { PayloadFilter } from '../api/types'

export interface FilterBuilderProps {
  collectionId: string
  value: PayloadFilter
  onChange: (f: PayloadFilter) => void
}

/**
 * Edits value.must only. Rows: key select (file_id, batch_id, tags, mime, element_type, chunk_strategy,
 * parse_strategy, page, chunk_index) + operator: keyword keys → "is any of" with a multi-select whose
 * options come from getFacet(collectionId, key) ("value (count)"); page/chunk_index → "between" with two
 * number inputs (gte/lte, empty = omitted). "Add condition" button appends {key: 'tags', match: {any: []}}
 * (not emitted until it has ≥1 value); "×" removes a row. Emits only complete conditions.
 */
export function FilterBuilder(_props: FilterBuilderProps): React.ReactElement {
  throw new Error('not implemented')
}
