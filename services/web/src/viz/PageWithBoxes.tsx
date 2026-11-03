import type { ParseArtifact } from '../api/types'
import { ELEMENT_COLORS } from '../lib/colors'

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
export function PageWithBoxes({
  imageUrl,
  width,
  height,
  elements,
  selectedId,
  onSelect,
}: PageWithBoxesProps): React.ReactElement {
  const boxes = elements
    .filter((el) => el.bbox !== null)
    .map((el) => ({
      id: el.id,
      type: el.type,
      title: `${el.type}: ${el.text.slice(0, 80)}`,
      left: (el.bbox!.l / width) * 100,
      top: (el.bbox!.t / height) * 100,
      boxWidth: ((el.bbox!.r - el.bbox!.l) / width) * 100,
      boxHeight: ((el.bbox!.b - el.bbox!.t) / height) * 100,
    }))
  const legendTypes = [...new Set(boxes.map((b) => b.type))]
  return (
    <section className="flex flex-col gap-3 p-4">
      <div
        className="relative w-full overflow-hidden rounded border border-gray-200"
        style={{ aspectRatio: `${width} / ${height}` }}
      >
        {imageUrl === null ? (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100 text-sm text-gray-500">
            No page image
          </div>
        ) : (
          <img src={imageUrl} alt="page" className="absolute inset-0 h-full w-full" />
        )}
        {boxes.map((b) => (
          <div
            key={b.id}
            data-testid="bbox"
            data-element-id={b.id}
            title={b.title}
            className="absolute cursor-pointer"
            style={{
              left: `${b.left}%`,
              top: `${b.top}%`,
              width: `${b.boxWidth}%`,
              height: `${b.boxHeight}%`,
              borderStyle: 'solid',
              borderColor: ELEMENT_COLORS[b.type],
              borderWidth: b.id === selectedId ? '3px' : '1px',
            }}
            onClick={() => onSelect?.(b.id)}
          />
        ))}
      </div>
      <ul className="flex flex-wrap gap-x-3 gap-y-1">
        {legendTypes.map((t) => (
          <li key={t} className="flex items-center gap-1 text-xs text-gray-600">
            <span
              className="h-2.5 w-2.5 rounded-sm"
              style={{ backgroundColor: ELEMENT_COLORS[t] }}
            />
            {t}
          </li>
        ))}
      </ul>
    </section>
  )
}
