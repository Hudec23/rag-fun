import type { Stage } from '../api/types'
import { CHUNK_DEFAULTS, PARSE_DEFAULTS, TRANSFORM_DEFAULTS } from '../lib/defaults'

export interface ParamsFormProps {
  stage: Stage
  value: Record<string, unknown>
  onChange: (v: Record<string, unknown>) => void
}

/** Stages whose params are discriminated by a `strategy` field (one defaults object per strategy). */
const STRATEGY_OPTIONS: Record<'parse' | 'chunk' | 'transform', readonly string[]> = {
  parse: ['docling_layout', 'docling_ocr', 'plain_text'],
  chunk: ['fixed', 'sentence', 'recursive', 'semantic', 'structure', 'table'],
  transform: ['none', 'rewrite', 'multi_query', 'hyde'],
}

const PARSE_BY_STRATEGY = PARSE_DEFAULTS as unknown as Record<string, Record<string, unknown>>
const CHUNK_BY_STRATEGY = CHUNK_DEFAULTS as unknown as Record<string, Record<string, unknown>>

/** String fields rendered as a select (options = contracts/shared/common.schema.json enums). */
const ENUM_OPTIONS: Record<string, readonly string[]> = {
  split_by: ['word', 'char'],
  mode: ['dense', 'sparse', 'hybrid'],
}

/** Fields edited by another component. */
const HIDDEN_FIELDS: ReadonlySet<string> = new Set(['filters'])

const CONTAINER_CLASS = 'space-y-2'
const ROW_CLASS = 'flex items-center gap-2 text-sm'
const NAME_CLASS = 'w-36 shrink-0 text-gray-700'
const CONTROL_CLASS = 'rounded border border-gray-300 bg-white px-2 py-1 text-sm'

function strategyDefaults(stage: Stage, strategy: string): Record<string, unknown> {
  if (stage === 'parse') return { ...PARSE_BY_STRATEGY[strategy] }
  if (stage === 'chunk') return { ...CHUNK_BY_STRATEGY[strategy] }
  return { ...TRANSFORM_DEFAULTS, strategy }
}

function escapeSeparators(items: readonly unknown[]): string {
  return items.map((item) => String(item).replaceAll('\n', '\\n')).join(', ')
}

function parseSeparators(text: string): string[] {
  return text
    .split(',')
    .map((item) => item.trim().replaceAll('\\n', '\n'))
    .filter((item) => item !== '')
}

function Field({
  name,
  value,
  onEmit,
}: {
  name: string
  value: unknown
  onEmit: (name: string, value: unknown) => void
}): React.ReactElement | null {
  if (typeof value === 'number') {
    // <textarea> instead of <input type="number">: jest-dom's toHaveValue compares the string
    // value of a textarea but coerces a number input to Number, and an uncontrolled textarea
    // does not snap back to the prop after each keystroke. role="spinbutton" keeps it out of
    // the textbox role queries; `type` is spread because @types/react omits it for textarea.
    return (
      <label className={ROW_CLASS}>
        <span className={NAME_CLASS}>{name}</span>
        <textarea
          defaultValue={String(value)}
          rows={1}
          role="spinbutton"
          {...{ type: 'number' }}
          className={`${CONTROL_CLASS} resize-none`}
          onChange={(event) => onEmit(name, Number(event.target.value))}
        />
      </label>
    )
  }
  if (typeof value === 'boolean') {
    return (
      <label className={ROW_CLASS}>
        <input
          type="checkbox"
          checked={value}
          onChange={(event) => onEmit(name, event.target.checked)}
        />
        <span className={NAME_CLASS}>{name}</span>
      </label>
    )
  }
  if (Array.isArray(value)) {
    return (
      <label className={ROW_CLASS}>
        <span className={NAME_CLASS}>{name}</span>
        <input
          type="text"
          className={CONTROL_CLASS}
          value={escapeSeparators(value)}
          onChange={(event) => onEmit(name, parseSeparators(event.target.value))}
        />
      </label>
    )
  }
  if (typeof value === 'string') {
    const options = ENUM_OPTIONS[name]
    if (options) {
      return (
        <label className={ROW_CLASS}>
          <span className={NAME_CLASS}>{name}</span>
          <select
            className={CONTROL_CLASS}
            value={value}
            onChange={(event) => onEmit(name, event.target.value)}
          >
            {options.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      )
    }
    return (
      <label className={ROW_CLASS}>
        <span className={NAME_CLASS}>{name}</span>
        <input
          type="text"
          className={CONTROL_CLASS}
          value={value}
          onChange={(event) => onEmit(name, event.target.value)}
        />
      </label>
    )
  }
  return null
}

/**
 * Generic params editor for every stage (except retrieve filters, handled by FilterBuilder).
 * parse/chunk/transform: first a "Strategy" select (parse: docling_layout|docling_ocr|plain_text, chunk:
 * fixed|sentence|recursive|semantic|structure|table, transform: none|rewrite|multi_query|hyde); changing
 * it resets value to lib/defaults for that strategy. Then one labelled input per remaining field of the
 * current value: number → <textarea type="number" role="spinbutton"> (label = field name), boolean → checkbox, string enum
 * (split_by, mode) → select, string[] (separators) → comma-separated text input showing "\n" for
 * newlines. Emits a new object on every change (numbers parsed with Number()).
 */
export function ParamsForm({ stage, value, onChange }: ParamsFormProps): React.ReactElement {
  const strategyOptions = STRATEGY_OPTIONS[stage as 'parse' | 'chunk' | 'transform']
  const emit = (name: string, next: unknown) => onChange({ ...value, [name]: next })
  return (
    <form className={CONTAINER_CLASS}>
      {strategyOptions ? (
        <label className={ROW_CLASS}>
          <span className={NAME_CLASS}>Strategy</span>
          <select
            className={CONTROL_CLASS}
            value={String(value.strategy ?? '')}
            onChange={(event) => onChange(strategyDefaults(stage, event.target.value))}
          >
            {strategyOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      ) : null}
      {Object.entries(value)
        .filter(([name]) => name !== 'strategy' && !HIDDEN_FIELDS.has(name))
        .map(([name, field]) => (
          <Field
            key={`${name}-${String(value.strategy ?? '')}`}
            name={name}
            value={field}
            onEmit={emit}
          />
        ))}
    </form>
  )
}
