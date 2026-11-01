import type { ChunkArtifact, EmbedArtifact } from '../../api/types'

export interface EmbedViewProps {
  stageRunId: string
  artifact: EmbedArtifact
  chunks?: ChunkArtifact['chunks']
}

/**
 * Header: "<n> chunks · <dense_model> (<dims>d) · <sparse_model>" + "<k> over limit" badge.
 * Tabs: "Tokens" (chunk selector + <TokenView>), "Heatmap" (<VectorHeatmap> of sampled chunks' dense
 * vectors, labels "#index"), "Projection" (method toggle PCA/UMAP + <ScatterPlot>, groups = chunk
 * element_type from the chunk artifact when given via props.chunks else 'chunk'), "Similarity"
 * (<SimilarityMatrix> labels "#index"). Notice: "Vectors are not stored yet — run Store to write them
 * to Qdrant."
 */
export function EmbedView(_props: EmbedViewProps): React.ReactElement {
  throw new Error('not implemented')
}
