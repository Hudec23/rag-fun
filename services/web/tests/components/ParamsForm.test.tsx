// ParamsForm (F-stage-flow): generic params editor per stage. parse/chunk/transform lead with a
// "Strategy" select that resets value to lib/defaults for the chosen strategy; the remaining fields
// render one labelled input each (number → number input, boolean → checkbox, string enum → select,
// string[] → comma text input). Every change emits a new object (numbers via Number()).
import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'

import { ParamsForm } from '../../src/components/ParamsForm'
import {
  CHUNK_DEFAULTS,
  EMBED_DEFAULTS,
  PARSE_DEFAULTS,
  RETRIEVE_DEFAULTS,
} from '../../src/lib/defaults'
import { renderWithProviders } from '../setup/render'

test('chunk recursive: Strategy select at recursive plus length, overlap and separators inputs', () => {
  const onChange = vi.fn()
  renderWithProviders(
    <ParamsForm stage="chunk" value={CHUNK_DEFAULTS.recursive} onChange={onChange} />,
  )
  expect(screen.getByRole('combobox', { name: 'Strategy' })).toHaveValue('recursive')
  const length = screen.getByLabelText('length')
  expect(length).toHaveAttribute('type', 'number')
  expect(length).toHaveValue('1000')
  const overlap = screen.getByLabelText('overlap')
  expect(overlap).toHaveAttribute('type', 'number')
  expect(overlap).toHaveValue('100')
  const separators = screen.getByRole('textbox', { name: 'separators' }) as HTMLInputElement
  expect(separators.value).toContain('sentence')
})

test('chunk: changing Strategy to semantic emits the semantic defaults', async () => {
  const onChange = vi.fn()
  const user = userEvent.setup()
  renderWithProviders(
    <ParamsForm stage="chunk" value={CHUNK_DEFAULTS.recursive} onChange={onChange} />,
  )
  await user.selectOptions(screen.getByRole('combobox', { name: 'Strategy' }), 'semantic')
  expect(onChange).toHaveBeenCalledTimes(1)
  expect(onChange).toHaveBeenCalledWith(CHUNK_DEFAULTS.semantic)
})

test('chunk: typing in length emits the value with length as a number', async () => {
  const onChange = vi.fn()
  const user = userEvent.setup()
  renderWithProviders(
    <ParamsForm stage="chunk" value={CHUNK_DEFAULTS.recursive} onChange={onChange} />,
  )
  const length = screen.getByLabelText('length')
  await user.clear(length)
  await user.type(length, '1500')
  expect(onChange).toHaveBeenLastCalledWith({
    strategy: 'recursive',
    length: 1500,
    overlap: 100,
    separators: ['\n\n', 'sentence', '\n', ' '],
  })
})

test('parse docling_layout: extract_tables and page_images checkboxes, toggling emits false', async () => {
  const onChange = vi.fn()
  const user = userEvent.setup()
  renderWithProviders(
    <ParamsForm stage="parse" value={PARSE_DEFAULTS.docling_layout} onChange={onChange} />,
  )
  const extract = screen.getByRole('checkbox', { name: 'extract_tables' })
  expect(extract).toBeChecked()
  const pageImages = screen.getByRole('checkbox', { name: 'page_images' })
  expect(pageImages).toBeChecked()
  await user.click(extract)
  expect(onChange).toHaveBeenCalledTimes(1)
  expect(onChange).toHaveBeenLastCalledWith({
    strategy: 'docling_layout',
    extract_tables: false,
    page_images: true,
  })
})

test('embed: only a batch_size number input, no Strategy select', () => {
  const onChange = vi.fn()
  renderWithProviders(<ParamsForm stage="embed" value={EMBED_DEFAULTS} onChange={onChange} />)
  const batch = screen.getByLabelText('batch_size')
  expect(batch).toHaveAttribute('type', 'number')
  expect(batch).toHaveValue('16')
  expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
  expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
  expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
})

test('retrieve: a mode select (dense/sparse/hybrid) and no filters field', () => {
  const onChange = vi.fn()
  renderWithProviders(<ParamsForm stage="retrieve" value={RETRIEVE_DEFAULTS} onChange={onChange} />)
  const mode = screen.getByRole('combobox', { name: 'mode' })
  expect(mode).toHaveValue('hybrid')
  expect(within(mode).getByRole('option', { name: 'dense' })).toBeInTheDocument()
  expect(within(mode).getByRole('option', { name: 'sparse' })).toBeInTheDocument()
  expect(within(mode).getByRole('option', { name: 'hybrid' })).toBeInTheDocument()
  expect(screen.queryByLabelText('filters')).not.toBeInTheDocument()
})
