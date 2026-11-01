import type { PipelineGraph } from '../api/types'

export interface PipelineGraphProps {
  graph: PipelineGraph
}

/**
 * @xyflow/react <ReactFlow> read-only: one node per graph.nodes (label = name, sublabel = class name
 * after the last '.', custom nodes highlighted with a purple border and "custom" badge), one edge per
 * graph.edges (label "sender_socket → receiver_socket"). Layout: nodes left-to-right in topological
 * order (x = depth*260, y = index within depth*110). Clicking a node shows its init_params as a
 * name/value table beside the graph.
 */
export function PipelineGraph(_props: PipelineGraphProps): React.ReactElement {
  throw new Error('not implemented')
}
