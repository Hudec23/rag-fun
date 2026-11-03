// F-parse (UI) — PageWithBoxes
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'

import { ELEMENT_COLORS } from '../../src/lib/colors'
import { PageWithBoxes } from '../../src/viz/PageWithBoxes'
import { PARSE } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

const PAGE = PARSE.pages[0]
const PAGE_1_ELEMENTS = PARSE.elements.filter((el) => el.page_no === 1)
const IMAGE_URL = '/api/v1/stage-runs/sr1/pages/1'

function renderPage(props: Partial<Parameters<typeof PageWithBoxes>[0]> = {}) {
  return renderWithProviders(
    <PageWithBoxes
      imageUrl={IMAGE_URL}
      width={PAGE.width}
      height={PAGE.height}
      elements={PAGE_1_ELEMENTS}
      {...props}
    />,
  )
}

test('renders one scaled bbox box per page-1 element', () => {
  renderPage()
  const boxes = screen.getAllByTestId('bbox')
  expect(boxes).toHaveLength(5)
  const [first] = boxes
  expect(first).toHaveAttribute('data-element-id', 'e-0000')
  expect(first).toHaveStyle({
    left: '11.76470588235294%', // 72/612*100
    top: '7.575757575757576%', // 60/792*100
  })
  expect(screen.getByAltText('page')).toHaveAttribute('src', IMAGE_URL)
})

test('gives each bbox box the border color of its element type', () => {
  renderPage()
  const boxes = screen.getAllByTestId('bbox')
  expect(boxes[0]).toHaveAttribute('data-element-id', 'e-0000')
  expect(boxes[0]).toHaveStyle({ borderColor: ELEMENT_COLORS.heading })
  expect(boxes[1]).toHaveAttribute('data-element-id', 'e-0001')
  expect(boxes[1]).toHaveStyle({ borderColor: ELEMENT_COLORS.text })
})

test('clicking a box selects it and the selected box has a thicker border', async () => {
  const onSelect = vi.fn()
  const user = userEvent.setup()
  const { unmount } = renderPage({ onSelect })
  const boxes = screen.getAllByTestId('bbox')
  const [first] = boxes
  expect(first).toHaveAttribute('data-element-id', 'e-0000')
  await user.click(first)
  expect(onSelect).toHaveBeenCalledTimes(1)
  expect(onSelect).toHaveBeenCalledWith('e-0000')
  unmount()
  renderPage({ selectedId: 'e-0000' })
  const [selected, unselected] = screen.getAllByTestId('bbox')
  expect(selected).toHaveAttribute('data-element-id', 'e-0000')
  expect(unselected).toHaveAttribute('data-element-id', 'e-0001')
  expect(selected.style.borderTopWidth).not.toBe(unselected.style.borderTopWidth)
})

test('draws a "No page image" placeholder with the boxes still rendered', () => {
  renderPage({ imageUrl: null })
  expect(screen.getByText('No page image')).toBeInTheDocument()
  expect(screen.getAllByTestId('bbox')).toHaveLength(5)
})

test('lists every element type present in the legend', () => {
  renderPage()
  expect(screen.getByText('heading')).toBeInTheDocument()
  expect(screen.getByText('text')).toBeInTheDocument()
  expect(screen.queryByText('table')).toBeNull()
})
