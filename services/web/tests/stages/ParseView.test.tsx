// F-parse (UI) — ParseView
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import type { ParseArtifact } from '../../src/api/types'
import { ParseView } from '../../src/components/stages/ParseView'
import { PARSE } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

const TABLE_ELEMENT: ParseArtifact['elements'][number] = {
  id: 'e-0008',
  type: 'table',
  text: '| Region | Revenue |\n| --- | --- |\n| Europe | 4.2 M |\n| US | 3.1 M |',
  page_no: 1,
  bbox: { l: 72, t: 260, r: 540, b: 320 },
  heading_level: null,
  section_path: [],
  table: {
    num_rows: 3,
    num_cols: 2,
    cells: [
      { row: 0, col: 0, row_span: 1, col_span: 1, text: 'Region', is_header: true },
      { row: 0, col: 1, row_span: 1, col_span: 1, text: 'Revenue', is_header: true },
      { row: 1, col: 0, row_span: 1, col_span: 1, text: 'Europe', is_header: false },
      { row: 1, col: 1, row_span: 1, col_span: 1, text: '4.2 M', is_header: false },
    ],
    markdown: '| Region | Revenue |\n| --- | --- |\n| Europe | 4.2 M |\n| US | 3.1 M |',
  },
  from_ocr: false,
  char_start: null,
  char_end: null,
}

const TABLE_ARTIFACT: ParseArtifact = { ...PARSE, elements: [...PARSE.elements, TABLE_ELEMENT] }

test('2 pages · 8 elements · 0 tables', () => {
  renderWithProviders(<ParseView stageRunId="sr1" artifact={PARSE} />)
  expect(screen.getByText('2 pages · 8 elements · 0 tables')).toBeInTheDocument()
  expect(screen.queryByText('OCR used')).toBeNull()
  expect(screen.getByAltText('page')).toHaveAttribute('src', '/api/v1/stage-runs/sr1/pages/1')
  expect(screen.getAllByTestId('bbox')).toHaveLength(5) // page 1
})

test('page select switches to page 2 boxes', async () => {
  const user = userEvent.setup()
  renderWithProviders(<ParseView stageRunId="sr1" artifact={PARSE} />)
  expect(screen.getAllByTestId('bbox')).toHaveLength(5) // page 1
  await user.selectOptions(screen.getByRole('combobox'), '2')
  expect(screen.getAllByTestId('bbox')).toHaveLength(3) // page 2
  expect(screen.getByAltText('page')).toHaveAttribute('src', '/api/v1/stage-runs/sr1/pages/2')
  expect(screen.getByText('Outlook')).toBeInTheDocument()
  expect(screen.queryByText('Q3 Report')).toBeNull()
})

test('selecting an element in the list highlights its box', async () => {
  const user = userEvent.setup()
  renderWithProviders(<ParseView stageRunId="sr1" artifact={PARSE} />)
  const boxById = (id: string) =>
    screen.getAllByTestId('bbox').find((el) => el.getAttribute('data-element-id') === id)!
  expect(boxById('e-0000')).toHaveStyle({ borderWidth: '1px' })
  await user.click(screen.getByText('Q3 Report'))
  expect(boxById('e-0000')).toHaveStyle({ borderWidth: '3px' })
})

test('tables render as <table> with <th> header cells', () => {
  renderWithProviders(<ParseView stageRunId="sr1" artifact={TABLE_ARTIFACT} />)
  expect(screen.getByRole('table')).toBeInTheDocument()
  const headers = screen.getAllByRole('columnheader')
  expect(headers).toHaveLength(2)
  expect(headers[0]).toHaveTextContent('Region')
  expect(headers[1]).toHaveTextContent('Revenue')
  const cells = screen.getAllByRole('cell')
  expect(cells).toHaveLength(2)
  expect(cells[0]).toHaveTextContent('Europe')
  expect(cells[1]).toHaveTextContent('4.2 M')
})
