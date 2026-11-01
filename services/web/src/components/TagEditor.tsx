export interface TagEditorProps {
  tags: string[]
  onChange: (tags: string[]) => void
}

/**
 * Chips for each tag with a "×" button (aria-label "remove <tag>"). Text input (aria-label "Add tag"):
 * Enter or ',' adds the trimmed lowercased value if it matches /^[a-z0-9][a-z0-9_.:-]*$/, is ≤64 chars and
 * not a duplicate; otherwise shows "invalid tag" and does not call onChange. Max 32 tags (input disabled).
 */
export function TagEditor(_props: TagEditorProps): React.ReactElement {
  throw new Error('not implemented')
}
