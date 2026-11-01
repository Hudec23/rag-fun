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
export function ScatterPlot(_props: ScatterPlotProps): React.ReactElement {
  throw new Error('not implemented')
}
