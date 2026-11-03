import Plot from 'react-plotly.js'

export interface LengthHistogramProps {
  binEdges: number[]
  counts: number[]
}

/**
 * Plotly bar chart (react-plotly.js <Plot>): x = bin centers ((edge[i]+edge[i+1])/2), y = counts,
 * width = bin width, layout title "Chunk length (chars)". Empty counts → text "No chunks".
 */
export function LengthHistogram({ binEdges, counts }: LengthHistogramProps): React.ReactElement {
  if (counts.length === 0) {
    return <p className="p-4 text-sm text-gray-500">No chunks</p>
  }
  const data = [
    {
      type: 'bar',
      x: counts.map((_count, i) => (binEdges[i] + binEdges[i + 1]) / 2),
      y: counts,
      width: counts.map((_count, i) => binEdges[i + 1] - binEdges[i]),
    },
  ]
  const layout = { title: 'Chunk length (chars)' }
  return <Plot data={data} layout={layout} />
}
