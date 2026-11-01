export interface LengthHistogramProps {
  binEdges: number[]
  counts: number[]
}

/**
 * Plotly bar chart (react-plotly.js <Plot>): x = bin centers ((edge[i]+edge[i+1])/2), y = counts,
 * width = bin width, layout title "Chunk length (chars)". Empty counts → text "No chunks".
 */
export function LengthHistogram(_props: LengthHistogramProps): React.ReactElement {
  throw new Error('not implemented')
}
