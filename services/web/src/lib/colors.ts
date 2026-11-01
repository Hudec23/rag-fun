/** Fixed colors per parse element type (bbox overlay, legends). Tailwind-independent hex values. */
export const ELEMENT_COLORS: Record<string, string> = {
  title: '#7c3aed',
  heading: '#2563eb',
  text: '#16a34a',
  list_item: '#0d9488',
  table: '#ea580c',
  picture: '#db2777',
  caption: '#ca8a04',
  formula: '#4f46e5',
  code: '#475569',
  footnote: '#78716c',
  page_header: '#9ca3af',
  page_footer: '#9ca3af',
}

/** 10 distinct colors for chunks, cycled by chunk index. */
export const CHUNK_COLORS = [
  '#fde68a',
  '#bfdbfe',
  '#bbf7d0',
  '#fecaca',
  '#ddd6fe',
  '#fbcfe8',
  '#a5f3fc',
  '#fed7aa',
  '#d9f99d',
  '#e5e7eb',
]
