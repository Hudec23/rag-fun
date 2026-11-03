import Plot from 'react-plotly.js'

export interface SimilarityMatrixProps {
  matrix: number[][]
  labels: string[]
}

/**
 * Plotly heatmap, z = matrix, x = y = labels, zmin -1, zmax 1, colorscale 'Viridis', title
 * "Cosine similarity". Below: the 5 most similar off-diagonal pairs (i<j) as "<label i> ↔ <label j>:
 * <value to 3 decimals>", sorted desc. Empty → "No vectors".
 */
export function SimilarityMatrix({ matrix, labels }: SimilarityMatrixProps): React.ReactElement {
  if (labels.length === 0 || matrix.length === 0) {
    return <p className="p-4 text-sm text-gray-500">No vectors</p>
  }
  const pairs: { i: number; j: number; value: number }[] = []
  for (let i = 0; i < labels.length; i++) {
    for (let j = i + 1; j < labels.length; j++) {
      pairs.push({ i, j, value: matrix[i][j] })
    }
  }
  pairs.sort((a, b) => b.value - a.value)
  const top = pairs.slice(0, 5)
  const data = [
    {
      type: 'heatmap',
      z: matrix,
      x: labels,
      y: labels,
      colorscale: 'Viridis',
      zmin: -1,
      zmax: 1,
    },
  ]
  const layout = { title: 'Cosine similarity' }
  return (
    <section className="p-4">
      <Plot data={data} layout={layout} />
      <ul className="mt-2 space-y-1 text-sm text-gray-700">
        {top.map((pair) => (
          <li key={`${pair.i}-${pair.j}`}>
            {labels[pair.i]} ↔ {labels[pair.j]}: {pair.value.toFixed(3)}
          </li>
        ))}
      </ul>
    </section>
  )
}
