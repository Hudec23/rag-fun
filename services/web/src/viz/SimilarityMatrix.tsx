export interface SimilarityMatrixProps {
  matrix: number[][]
  labels: string[]
}

/**
 * Plotly heatmap, z = matrix, x = y = labels, zmin -1, zmax 1, colorscale 'Viridis', title
 * "Cosine similarity". Below: the 5 most similar off-diagonal pairs (i<j) as "<label i> ↔ <label j>:
 * <value to 3 decimals>", sorted desc. Empty → "No vectors".
 */
export function SimilarityMatrix(_props: SimilarityMatrixProps): React.ReactElement {
  throw new Error('not implemented')
}
