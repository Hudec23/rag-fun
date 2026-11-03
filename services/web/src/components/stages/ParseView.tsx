import { useState } from 'react'

import { pageImageUrl } from '../../api/runs'
import type { ParseArtifact } from '../../api/types'
import { ELEMENT_COLORS } from '../../lib/colors'
import { PageWithBoxes } from '../../viz/PageWithBoxes'

export interface ParseViewProps {
  stageRunId: string
  artifact: ParseArtifact
}

type ParseElement = ParseArtifact['elements'][number]
type ParseTable = NonNullable<ParseElement['table']>

/** HTML <table> from table.cells; is_header cells render as <th>, spans become rowSpan/colSpan. */
function TableCells({ table }: { table: ParseTable }): React.ReactElement {
  const { num_rows, num_cols, cells } = table
  const taken: (ParseTable['cells'][number] | null)[][] = Array.from({ length: num_rows }, () =>
    Array.from({ length: num_cols }, () => null),
  )
  for (const c of cells) {
    if (c.row >= num_rows || c.col >= num_cols || taken[c.row][c.col] !== null) continue
    for (let r = c.row; r < Math.min(num_rows, c.row + c.row_span); r++) {
      for (let col = c.col; col < Math.min(num_cols, c.col + c.col_span); col++) {
        taken[r][col] = r === c.row && col === c.col ? c : null
      }
    }
  }
  return (
    <table className="w-full border-collapse text-xs">
      <tbody>
        {taken.map((row, r) => (
          <tr key={r}>
            {row.map((c, col) =>
              c === null ? null : c.is_header ? (
                <th
                  key={col}
                  rowSpan={c.row_span}
                  colSpan={c.col_span}
                  className="border border-gray-300 bg-gray-100 px-2 py-1 text-left font-medium"
                >
                  {c.text}
                </th>
              ) : (
                <td
                  key={col}
                  rowSpan={c.row_span}
                  colSpan={c.col_span}
                  className="border border-gray-300 px-2 py-1"
                >
                  {c.text}
                </td>
              ),
            )}
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function ElementList({
  elements,
  selectedId,
  onSelect,
}: {
  elements: ParseElement[]
  selectedId: string | null
  onSelect: (id: string) => void
}): React.ReactElement {
  return (
    <ul className="flex flex-col gap-2">
      {elements.map((el) => (
        <li
          key={el.id}
          className={`flex cursor-pointer items-start gap-2 rounded border p-2 text-sm ${
            el.id === selectedId ? 'border-blue-600 ring-1 ring-blue-600' : 'border-gray-200'
          }`}
          onClick={() => onSelect(el.id)}
        >
          <span
            className="rounded-sm px-1.5 py-0.5 text-xs font-medium text-white"
            style={{ backgroundColor: ELEMENT_COLORS[el.type] }}
          >
            {el.type}
          </span>
          {el.type === 'table' && el.table ? (
            <div className="flex-1">
              <TableCells table={el.table} />
            </div>
          ) : (
            <span className="flex-1 whitespace-pre-wrap break-words">{el.text}</span>
          )}
        </li>
      ))}
    </ul>
  )
}

/**
 * Left: page selector (pages[]) + <PageWithBoxes> using pageImageUrl(stageRunId, page). Right:
 * element list for the page (type badge in ELEMENT_COLORS, text); selecting an element in either place
 * selects it in both. Tables render as an HTML <table> from table.cells (header cells as <th>).
 * Header line: "<n> pages · <m> elements · <t> tables" + "OCR used" badge when ocr_used. Formats
 * without pages: just the element list.
 */
export function ParseView({ stageRunId, artifact }: ParseViewProps): React.ReactElement {
  const { pages, elements, ocr_used } = artifact
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [pageNo, setPageNo] = useState<number | null>(() => pages[0]?.page_no ?? null)

  const tableCount = elements.filter((el) => el.type === 'table').length
  const page = pages.length > 0 ? (pages.find((p) => p.page_no === pageNo) ?? pages[0]) : null
  const pageElements = page ? elements.filter((el) => el.page_no === page.page_no) : elements

  return (
    <section className="flex flex-col gap-3 p-4">
      <header className="flex items-center gap-2 text-sm">
        <span>
          {pages.length} pages · {elements.length} elements · {tableCount} tables
        </span>
        {ocr_used ? (
          <span className="rounded bg-amber-100 px-1.5 py-0.5 text-xs font-medium text-amber-800">
            OCR used
          </span>
        ) : null}
      </header>
      {page ? (
        <div className="flex flex-col gap-4 lg:flex-row">
          <div className="flex-1">
            <label className="mb-2 flex items-center gap-2 text-sm">
              Page
              <select
                value={String(pageNo ?? '')}
                onChange={(e) => setPageNo(Number(e.target.value))}
                className="rounded border border-gray-300 bg-white p-1"
              >
                {pages.map((p) => (
                  <option key={p.page_no} value={p.page_no}>
                    {p.page_no}
                  </option>
                ))}
              </select>
            </label>
            <PageWithBoxes
              imageUrl={pageImageUrl(stageRunId, page.page_no)}
              width={page.width}
              height={page.height}
              elements={pageElements}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
          </div>
          <div className="w-full lg:w-96">
            <ElementList elements={pageElements} selectedId={selectedId} onSelect={setSelectedId} />
          </div>
        </div>
      ) : (
        <ElementList elements={pageElements} selectedId={selectedId} onSelect={setSelectedId} />
      )}
    </section>
  )
}
