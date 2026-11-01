import type { Stage } from '../api/types'

export interface ParamsFormProps {
  stage: Stage
  value: Record<string, unknown>
  onChange: (v: Record<string, unknown>) => void
}

/**
 * Generic params editor for every stage (except retrieve filters, handled by FilterBuilder).
 * parse/chunk/transform: first a "Strategy" select (parse: docling_layout|docling_ocr|plain_text, chunk:
 * fixed|sentence|recursive|semantic|structure|table, transform: none|rewrite|multi_query|hyde); changing
 * it resets value to lib/defaults for that strategy. Then one labelled input per remaining field of the
 * current value: number → <input type="number"> (label = field name), boolean → checkbox, string enum
 * (split_by, mode) → select, string[] (separators) → comma-separated text input showing "\n" for
 * newlines. Emits a new object on every change (numbers parsed with Number()).
 */
export function ParamsForm(_props: ParamsFormProps): React.ReactElement {
  throw new Error('not implemented')
}
