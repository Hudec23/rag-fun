import { useState } from 'react'

export interface TagEditorProps {
  tags: string[]
  onChange: (tags: string[]) => void
}

const TAG_RE = /^[a-z0-9][a-z0-9_.:-]*$/
const MAX_TAG_LEN = 64
const MAX_TAGS = 32

/**
 * Chips for each tag with a "×" button (aria-label "remove <tag>"). Text input (aria-label "Add tag"):
 * Enter or ',' adds the trimmed lowercased value if it matches /^[a-z0-9][a-z0-9_.:-]*$/, is ≤64 chars and
 * not a duplicate; otherwise shows "invalid tag" and does not call onChange. Max 32 tags (input disabled).
 */
export function TagEditor({ tags, onChange }: TagEditorProps): React.ReactElement {
  const [draft, setDraft] = useState('')
  const [invalid, setInvalid] = useState(false)
  const atLimit = tags.length >= MAX_TAGS

  const addTag = () => {
    const value = draft.trim().toLowerCase()
    if (value.length <= MAX_TAG_LEN && TAG_RE.test(value) && !tags.includes(value)) {
      onChange([...tags, value])
      setDraft('')
      setInvalid(false)
    } else {
      setInvalid(true)
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <ul className="flex flex-wrap gap-1">
        {tags.map((tag) => (
          <li key={tag} className="flex items-center gap-1 rounded bg-gray-100 px-2 py-0.5 text-sm">
            <span>{tag}</span>
            <button
              type="button"
              aria-label={`remove ${tag}`}
              onClick={() => onChange(tags.filter((t) => t !== tag))}
              className="text-gray-500 hover:text-gray-700"
            >
              ×
            </button>
          </li>
        ))}
      </ul>
      <input
        aria-label="Add tag"
        value={draft}
        disabled={atLimit}
        onChange={(e) => {
          setDraft(e.target.value)
          setInvalid(false)
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault()
            addTag()
          }
        }}
        className="w-40 rounded border px-2 py-1 text-sm"
      />
      {invalid && <span className="text-sm text-red-600">invalid tag</span>}
    </div>
  )
}
