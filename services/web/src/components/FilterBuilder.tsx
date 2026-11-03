import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getFacet } from '../api/qdrant'
import type { FilterCondition, PayloadFilter } from '../api/types'

export interface FilterBuilderProps {
  collectionId: string
  value: PayloadFilter
  onChange: (f: PayloadFilter) => void
}

const KEY_OPTIONS = [
  'file_id',
  'batch_id',
  'tags',
  'mime',
  'element_type',
  'chunk_strategy',
  'parse_strategy',
  'page',
  'chunk_index',
] as const
type KeyOption = (typeof KEY_OPTIONS)[number]

const CONTROL_CLASS = 'rounded border border-gray-300 bg-white px-2 py-1 text-sm'

interface Row {
  id: number
  key: KeyOption
  any: string[]
  from: string
  to: string
}

let nextRowId = 0

function newRow(): Row {
  nextRowId += 1
  return { id: nextRowId, key: 'tags', any: [], from: '', to: '' }
}

function rowFromCondition(condition: FilterCondition): Row {
  const row = newRow()
  row.key = condition.key
  if ('range' in condition) {
    row.from = condition.range.gte !== undefined ? String(condition.range.gte) : ''
    row.to = condition.range.lte !== undefined ? String(condition.range.lte) : ''
  } else if ('any' in condition.match) {
    row.any = condition.match.any.map(String)
  } else {
    row.any = [String(condition.match.value)]
  }
  return row
}

function conditionFromRow(row: Row): FilterCondition | null {
  if (row.key === 'page' || row.key === 'chunk_index') {
    const gte = parseBound(row.from)
    const lte = parseBound(row.to)
    if (gte === undefined && lte === undefined) return null
    const range: { gte?: number; lte?: number } = {}
    if (gte !== undefined) range.gte = gte
    if (lte !== undefined) range.lte = lte
    return { key: row.key, range }
  }
  if (row.any.length === 0) return null
  return { key: row.key, match: { any: row.any } }
}

function parseBound(raw: string): number | undefined {
  const trimmed = raw.trim()
  if (trimmed === '') return undefined
  const parsed = Number(trimmed)
  return Number.isNaN(parsed) ? undefined : parsed
}

interface ConditionRowProps {
  collectionId: string
  row: Row
  onChange: (rowId: number, patch: Partial<Row>) => void
  onRemove: (rowId: number) => void
}

function ConditionRow({
  collectionId,
  row,
  onChange,
  onRemove,
}: ConditionRowProps): React.ReactElement {
  const numeric = row.key === 'page' || row.key === 'chunk_index'
  const { data } = useQuery({
    queryKey: ['facet', collectionId, row.key],
    queryFn: () => getFacet(collectionId, row.key),
    enabled: !numeric,
  })
  return (
    <div className="flex flex-wrap items-center gap-2">
      <select
        aria-label="key"
        className={CONTROL_CLASS}
        value={row.key}
        onChange={(event) => onChange(row.id, { key: event.target.value as KeyOption })}
      >
        {KEY_OPTIONS.map((key) => (
          <option key={key} value={key}>
            {key}
          </option>
        ))}
      </select>
      {numeric ? (
        <>
          <span className="text-sm text-gray-700">between</span>
          <input
            type="number"
            aria-label="from"
            className={CONTROL_CLASS}
            value={row.from}
            onChange={(event) => onChange(row.id, { from: event.target.value })}
          />
          <input
            type="number"
            aria-label="to"
            className={CONTROL_CLASS}
            value={row.to}
            onChange={(event) => onChange(row.id, { to: event.target.value })}
          />
        </>
      ) : (
        <>
          <span className="text-sm text-gray-700">is any of</span>
          <select
            multiple
            aria-label="values"
            className={`${CONTROL_CLASS} h-24`}
            value={row.any}
            onChange={(event) =>
              onChange(row.id, {
                any: Array.from(event.target.selectedOptions, (option) => option.value),
              })
            }
          >
            {(data?.values ?? []).map((facet) => (
              <option key={facet.value} value={facet.value}>
                {`${facet.value} (${facet.count})`}
              </option>
            ))}
          </select>
        </>
      )}
      <button
        type="button"
        aria-label="remove condition"
        className={CONTROL_CLASS}
        onClick={() => onRemove(row.id)}
      >
        ×
      </button>
    </div>
  )
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
export function FilterBuilder({
  collectionId,
  value,
  onChange,
}: FilterBuilderProps): React.ReactElement {
  const [rows, setRows] = useState<Row[]>(() => (value.must ?? []).map(rowFromCondition))

  const commit = (next: Row[]) => {
    setRows(next)
    const complete = next.map(conditionFromRow).filter((c): c is FilterCondition => c !== null)
    if (JSON.stringify(complete) === JSON.stringify(value.must ?? [])) return
    onChange({ ...value, must: complete })
  }

  const updateRow = (rowId: number, patch: Partial<Row>) => {
    const next = rows.map((row) => {
      if (row.id !== rowId) return row
      const merged = { ...row, ...patch }
      return patch.key !== undefined && patch.key !== row.key
        ? { ...merged, any: [], from: '', to: '' }
        : merged
    })
    commit(next)
  }

  const removeRow = (rowId: number) => {
    commit(rows.filter((row) => row.id !== rowId))
  }

  return (
    <div className="space-y-2">
      {rows.map((row) => (
        <ConditionRow
          key={row.id}
          collectionId={collectionId}
          row={row}
          onChange={updateRow}
          onRemove={removeRow}
        />
      ))}
      <button type="button" className={CONTROL_CLASS} onClick={() => commit([...rows, newRow()])}>
        Add condition
      </button>
    </div>
  )
}
