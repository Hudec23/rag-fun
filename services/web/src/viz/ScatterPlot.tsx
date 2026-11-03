import Plot from 'react-plotly.js'
import { useState } from 'react'

export interface ScatterPlotProps {
  points2d: number[][] | null
  points3d: number[][] | null
  labels: string[]
  groups: string[]
  method: 'pca' | 'umap'
}

/**
 * Toggle buttons "2D" / "3D" (default 2D). 2D → Plotly 'scatter' mode markers; 3D → 'scatter3d'.
 * One trace per distinct group (legend), hover text = labels[i]. Selected dimension's points null →
 * message "Not enough chunks for <METHOD> <2D|3D>". Title "<PCA|UMAP> projection".
 */
export function ScatterPlot({
  points2d,
  points3d,
  labels,
  groups,
  method,
}: ScatterPlotProps): React.ReactElement {
  const [dimension, setDimension] = useState<'2d' | '3d'>('2d')
  const methodLabel = method === 'pca' ? 'PCA' : 'UMAP'
  const dimensionLabel = dimension === '2d' ? '2D' : '3D'
  const points = dimension === '2d' ? points2d : points3d
  const buttonClass = (active: boolean) =>
    `rounded border px-2 py-1 text-sm ${
      active ? 'border-gray-900 bg-gray-900 text-white' : 'border-gray-300 bg-white text-gray-700'
    }`

  const groupIndices = new Map<string, number[]>()
  groups.forEach((group, index) => {
    const indices = groupIndices.get(group)
    if (indices === undefined) {
      groupIndices.set(group, [index])
    } else {
      indices.push(index)
    }
  })
  const data =
    points === null
      ? []
      : [...groupIndices.entries()].map(([name, indices]) => ({
          type: dimension === '2d' ? 'scatter' : 'scatter3d',
          name,
          mode: 'markers',
          x: indices.map((i) => points[i][0]),
          y: indices.map((i) => points[i][1]),
          ...(dimension === '3d' ? { z: indices.map((i) => points[i][2]) } : null),
          text: indices.map((i) => labels[i]),
          hovertext: indices.map((i) => labels[i]),
        }))
  const layout = { title: `${methodLabel} projection` }

  return (
    <section className="p-4">
      <div className="mb-2 flex gap-1">
        <button
          type="button"
          className={buttonClass(dimension === '2d')}
          onClick={() => setDimension('2d')}
        >
          2D
        </button>
        <button
          type="button"
          className={buttonClass(dimension === '3d')}
          onClick={() => setDimension('3d')}
        >
          3D
        </button>
      </div>
      {points === null ? (
        <p className="text-sm text-gray-500">
          Not enough chunks for {methodLabel} {dimensionLabel}
        </p>
      ) : (
        <Plot data={data} layout={layout} />
      )}
    </section>
  )
}
