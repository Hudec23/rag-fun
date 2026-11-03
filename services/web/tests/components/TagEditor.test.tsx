// TagEditor (F-upload): chips, add on Enter/comma, validation, 32-tag limit.
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'

import { TagEditor } from '../../src/components/TagEditor'
import { renderWithProviders } from '../setup/render'

test('renders chips with remove buttons and removes a tag on click', async () => {
  const onChange = vi.fn()
  const user = userEvent.setup()
  renderWithProviders(<TagEditor tags={['a', 'b']} onChange={onChange} />)
  expect(screen.getByText('a')).toBeInTheDocument()
  expect(screen.getByText('b')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'remove a' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'remove b' })).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'remove a' }))
  expect(onChange).toHaveBeenCalledTimes(1)
  expect(onChange).toHaveBeenLastCalledWith(['b'])
})

test('adds a lowercased tag on Enter', async () => {
  const onChange = vi.fn()
  const user = userEvent.setup()
  renderWithProviders(<TagEditor tags={['a', 'b']} onChange={onChange} />)
  await user.type(screen.getByLabelText('Add tag'), 'Finance{Enter}')
  expect(onChange).toHaveBeenCalledTimes(1)
  expect(onChange).toHaveBeenLastCalledWith(['a', 'b', 'finance'])
})

test('adds a tag on comma', async () => {
  const onChange = vi.fn()
  const user = userEvent.setup()
  renderWithProviders(<TagEditor tags={['a', 'b']} onChange={onChange} />)
  await user.type(screen.getByLabelText('Add tag'), 'x,')
  expect(onChange).toHaveBeenCalledTimes(1)
  expect(onChange).toHaveBeenLastCalledWith(['a', 'b', 'x'])
})

test('shows invalid tag and does not call onChange for an invalid value', async () => {
  const onChange = vi.fn()
  const user = userEvent.setup()
  renderWithProviders(<TagEditor tags={['a', 'b']} onChange={onChange} />)
  await user.type(screen.getByLabelText('Add tag'), 'bad tag!{Enter}')
  expect(screen.getByText('invalid tag')).toBeInTheDocument()
  expect(onChange).not.toHaveBeenCalled()
})

test('does not add duplicates and shows invalid tag for 65-char tags', async () => {
  const onChange = vi.fn()
  const user = userEvent.setup()
  renderWithProviders(<TagEditor tags={['a']} onChange={onChange} />)
  const input = screen.getByLabelText('Add tag')
  await user.type(input, 'a{Enter}')
  expect(onChange).not.toHaveBeenCalled()
  await user.clear(input)
  await user.type(input, `${'a'.repeat(65)}{Enter}`)
  expect(onChange).not.toHaveBeenCalled()
  expect(screen.getByText('invalid tag')).toBeInTheDocument()
})

test('disables the input at 32 tags', () => {
  const onChange = vi.fn()
  renderWithProviders(
    <TagEditor tags={Array.from({ length: 32 }, (_, i) => `tag-${i}`)} onChange={onChange} />,
  )
  expect(screen.getByLabelText('Add tag')).toBeDisabled()
})
