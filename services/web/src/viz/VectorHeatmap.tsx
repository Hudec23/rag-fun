import Plot from 'react-plotly.js'

export interface VectorHeatmapProps {
  vectors: number[][]
  labels: string[]
}

/**
 * Plotly heatmap: z = vectors (rows = chunks, labels on y), x = dimension index, colorscale 'RdBu',
 * zmid 0, layout title "Dense vectors (<n> × <dims>)". Empty → "No vectors".
 */
export function VectorHeatmap({ vectors, labels }: VectorHeatmapProps): React.ReactElement {
  if (vectors.length === 0) {
    return <p className="p-4 text-sm text-gray-500">No vectors</p>
  }
  const dims = vectors[0].length
  const data = [
    {
      type: 'heatmap',
      z: vectors,
      x: vectors[0].map((_v, i) => i),
      y: labels,
      colorscale: 'RdBu',
      zmid: 0,
    },
  ]
  const layout = { title: `Dense vectors (${vectors.length} × ${dims})` }
  return <Plot data={data} layout={layout} />
}
