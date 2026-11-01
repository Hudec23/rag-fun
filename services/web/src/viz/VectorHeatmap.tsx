export interface VectorHeatmapProps {
  vectors: number[][]
  labels: string[]
}

/**
 * Plotly heatmap: z = vectors (rows = chunks, labels on y), x = dimension index, colorscale 'RdBu',
 * zmid 0, layout title "Dense vectors (<n> × <dims>)". Empty → "No vectors".
 */
export function VectorHeatmap(_props: VectorHeatmapProps): React.ReactElement {
  throw new Error('not implemented')
}
