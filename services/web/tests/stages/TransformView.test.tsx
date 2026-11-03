// F-transform (UI) — TransformView
import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import type { TransformArtifact } from '../../src/api/types'
import { TransformView } from '../../src/components/stages/TransformView'
import { TRANSFORM } from '../setup/fixtures'
import { renderWithProviders } from '../setup/render'

const HYDE_DOC = 'A hypothetical document about how subscription revenue changed in Q3.'

// Same artifact with the hyde strategy: the hypothetical document is the search query.
const HYDE: TransformArtifact = {
  ...TRANSFORM,
  strategy: 'hyde',
  queries: [HYDE_DOC],
  hyde_document: HYDE_DOC,
}

// Same artifact with no transformation: the question is used as is.
const NONE: TransformArtifact = {
  ...TRANSFORM,
  strategy: 'none',
  queries: [TRANSFORM.question],
  hyde_document: null,
  messages: [],
  model: null,
}

test('queries listed under "Search queries"', () => {
  renderWithProviders(<TransformView stageRunId="sr4" artifact={TRANSFORM} />)
  expect(screen.getByText('Search queries')).toBeInTheDocument()
  const items = screen.getAllByRole('list').flatMap((list) => within(list).getAllByRole('listitem'))
  expect(items.map((item) => item.textContent)).toEqual(TRANSFORM.queries)
})

test('hyde artifact → quote block with hyde_document', () => {
  renderWithProviders(<TransformView stageRunId="sr4" artifact={HYDE} />)
  expect(screen.getByText(HYDE_DOC).closest('blockquote')).not.toBeNull()
})

test('strategy none → No transformation — the question is used as is.', () => {
  renderWithProviders(<TransformView stageRunId="sr4" artifact={NONE} />)
  expect(screen.getByText('No transformation — the question is used as is.')).toBeInTheDocument()
  expect(screen.queryByText('Search queries')).toBeNull()
})

test('"Prompt" collapsible shows system message', async () => {
  const user = userEvent.setup()
  renderWithProviders(<TransformView stageRunId="sr4" artifact={TRANSFORM} />)
  await user.click(screen.getByText('Prompt'))
  expect(screen.getByText(TRANSFORM.messages[0].role)).toBeInTheDocument()
  expect(screen.getByText(TRANSFORM.messages[0].content)).toBeInTheDocument()
})
