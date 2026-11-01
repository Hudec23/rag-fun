import type { ParseArtifact } from '../api/types'

export interface PageWithBoxesProps {
  imageUrl: string | null
  width: number
  height: number
  elements: ParseArtifact['elements']
  selectedId?: string | null
  onSelect?: (elementId: string) => void
}

/**
 * Page image (<img alt="page">) in a relative container; for every element with a bbox an absolutely
 * positioned <div data-testid="bbox" data-element-id=…> at left/top/width/height in % of the page
 * (l/width*100, t/height*100, (r-l)/width*100, (b-t)/height*100), border color ELEMENT_COLORS[type],
 * title = "<type>: <first 80 chars of text>". Click → onSelect(id). selectedId gets a thicker border.
 * imageUrl null → grey placeholder "No page image" with the boxes still drawn on a width:height box.
 * Legend below: one entry per element type present.
 */
export function PageWithBoxes(_props: PageWithBoxesProps): React.ReactElement {
  throw new Error('not implemented')
}
