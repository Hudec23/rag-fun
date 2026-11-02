import type { ChunkArtifact, EmbedArtifact } from '../../api/types'

export interface EmbedViewProps {
  stageRunId: string
  artifact: EmbedArtifact
  chunks?: ChunkArtifact['chunks']
}

/**
 * Header: "<n> chunks · <dense_model> (<dims>d) · <sparse_model>" + "<k> over limit" badge. Tabs are
 * <button role="tab"> (accessible name = label) above one <div role="tabpanel">: "Tokens" (chunk
 * selector + <TokenView>), "Heatmap" (<VectorHeatmap> of sampled chunks' dense vectors, labels "#index"),
 * "Projection" (two buttons named exactly "PCA" and "UMAP", default PCA, + <ScatterPlot>; groups =
 * element_type of props.chunks when given, else 'chunk'), "Similarity" (<SimilarityMatrix> labels
 * "#index"). Notice: "Vectors are not stored yet — run Store to write them to Qdrant."
 */
export function EmbedView(_props: EmbedViewProps): React.ReactElement {
  throw new Error('not implemented')
}
