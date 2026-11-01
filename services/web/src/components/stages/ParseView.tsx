import type { ParseArtifact } from '../../api/types'

export interface ParseViewProps {
  stageRunId: string
  artifact: ParseArtifact
}

/**
 * Left: page selector (pages[]) + <PageWithBoxes> using pageImageUrl(stageRunId, page). Right:
 * element list for the page (type badge in ELEMENT_COLORS, text); selecting an element in either place
 * selects it in both. Tables render as an HTML <table> from table.cells (header cells as <th>).
 * Header line: "<n> pages · <m> elements · <t> tables" + "OCR used" badge when ocr_used. Formats
 * without pages: just the element list.
 */
export function ParseView(_props: ParseViewProps): React.ReactElement {
  throw new Error('not implemented')
}
