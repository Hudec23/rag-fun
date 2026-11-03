import { useMemo, useState } from 'react'
import {
  BaseEdge,
  EdgeLabelRenderer,
  Handle,
  Position,
  ReactFlow,
  getSmoothStepPath,
  type Edge,
  type EdgeProps,
  type Node,
  type NodeMouseHandler,
  type NodeProps,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import type { PipelineGraph } from '../api/types'

export interface PipelineGraphProps {
  graph: PipelineGraph
}

const DEPTH_X = 260
const LANE_Y = 110
const NODE_W = 140
const NODE_H = 48

/**
 * Static node dimensions and handles so @xyflow can compute edge positions without measuring the
 * DOM (its `getEdgePosition` bails when node dimensions/handles are unknown, which is always the
 * case in jsdom). Real browsers still re-measure the handles on mount.
 */
function nodeHandles(): Node['handles'] {
  return [
    {
      id: 'target',
      type: 'target',
      position: Position.Left,
      x: 0,
      y: NODE_H / 2,
      width: 0,
      height: 0,
    },
    {
      id: 'source',
      type: 'source',
      position: Position.Right,
      x: NODE_W,
      y: NODE_H / 2,
      width: 0,
      height: 0,
    },
  ]
}

type CardData = {
  label: string
  sublabel: string
  custom: boolean
}

type CardNode = Node<CardData, 'card'>

/** Class name after the last '.', e.g. `...document_splitter.DocumentSplitter` → `DocumentSplitter`. */
function sublabel(type: string): string {
  const dot = type.lastIndexOf('.')
  return dot === -1 ? type : type.slice(dot + 1)
}

/** Depth of every graph node: 0 for nodes without incoming edges, else 1 + the max depth of their
 * senders (topological). Cycles stop extending and are reported at the current depth. */
function depths(graph: PipelineGraph): number[] {
  const incoming = new Map<string, string[]>()
  for (const edge of graph.edges) {
    const senders = incoming.get(edge.receiver)
    if (senders !== undefined) senders.push(edge.sender)
    else incoming.set(edge.receiver, [edge.sender])
  }
  const depth = new Map<string, number>()
  const visiting = new Set<string>()
  const depthOf = (name: string): number => {
    const cached = depth.get(name)
    if (cached !== undefined) return cached
    if (visiting.has(name)) return 0
    visiting.add(name)
    const senders = incoming.get(name) ?? []
    const value = senders.length > 0 ? Math.max(...senders.map(depthOf)) + 1 : 0
    visiting.delete(name)
    depth.set(name, value)
    return value
  }
  return graph.nodes.map((node) => depthOf(node.name))
}

function buildNodes(graph: PipelineGraph): CardNode[] {
  const nodeDepths = depths(graph)
  const lane = new Map<number, number>()
  return graph.nodes.map((node, i) => {
    const d = nodeDepths[i]
    const row = lane.get(d) ?? 0
    lane.set(d, row + 1)
    return {
      id: node.name,
      type: 'card',
      position: { x: d * DEPTH_X, y: row * LANE_Y },
      width: NODE_W,
      height: NODE_H,
      handles: nodeHandles(),
      data: { label: node.name, sublabel: sublabel(node.type), custom: node.custom },
    }
  })
}

function buildEdges(graph: PipelineGraph): Edge[] {
  return graph.edges.map((edge, i) => ({
    id: `${edge.sender}-${i}`,
    source: edge.sender,
    target: edge.receiver,
    type: 'pipe',
    label: `${edge.sender_socket} → ${edge.receiver_socket}`,
  }))
}

/**
 * Smooth step line between the source (right side) and the target (left side) with the socket
 * label centred on the line. The label goes through the div-based <EdgeLabelRenderer /> portal
 * because <EdgeText /> measures its width with SVG getBBox(), which jsdom does not implement.
 */
function PipeEdge(props: EdgeProps): React.ReactElement {
  const { sourceX, sourceY, targetX, targetY, label } = props
  const [path, centerX, centerY] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition: Position.Right,
    targetX,
    targetY,
    targetPosition: Position.Left,
    borderRadius: 12,
  })
  return (
    <>
      <BaseEdge path={path} />
      <EdgeLabelRenderer>
        <div
          className="nodrag nopan absolute rounded bg-white px-1.5 py-0.5 text-xs text-gray-600 ring-1 ring-gray-200"
          style={{ transform: `translate(-50%, -50%) translate(${centerX}px, ${centerY}px)` }}
        >
          {label}
        </div>
      </EdgeLabelRenderer>
    </>
  )
}

function NodeCard(props: NodeProps<CardNode>): React.ReactElement {
  const { label, sublabel, custom } = props.data
  return (
    <div
      className={
        custom
          ? 'rounded border-2 border-purple-500 bg-white px-2 py-1.5 shadow-sm'
          : 'rounded border border-gray-300 bg-white px-2 py-1.5 shadow-sm'
      }
    >
      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
      <div className="text-sm font-medium text-gray-700">{label}</div>
      <div className="text-xs text-gray-500">{sublabel}</div>
      {custom ? (
        <span className="mt-1 inline-block rounded bg-purple-100 px-1.5 py-0.5 text-[10px] font-semibold text-purple-700">
          custom
        </span>
      ) : null}
    </div>
  )
}

const cardNodeTypes = { card: NodeCard }
const pipeEdgeTypes = { pipe: PipeEdge }

/**
 * @xyflow/react <ReactFlow> read-only: one node per graph.nodes (label = name, sublabel = class name
 * after the last '.', custom nodes highlighted with a purple border and "custom" badge), one edge per
 * graph.edges (label "sender_socket → receiver_socket"). Layout: nodes left-to-right in topological
 * order (x = depth*260, y = index within depth*110). Clicking a node shows its init_params as a
 * name/value table beside the graph.
 */
export function PipelineGraph({ graph }: PipelineGraphProps): React.ReactElement {
  const [selectedName, setSelectedName] = useState<string | null>(null)
  const nodes = useMemo(() => buildNodes(graph), [graph])
  const edges = useMemo(() => buildEdges(graph), [graph])
  const selected =
    selectedName !== null ? (graph.nodes.find((node) => node.name === selectedName) ?? null) : null

  const onNodeClick: NodeMouseHandler<CardNode> = (_event, node) => {
    setSelectedName(node.id)
  }

  return (
    <div className="flex flex-col gap-4 xl:flex-row">
      <div
        className="min-w-0 flex-1 overflow-hidden rounded border border-gray-200"
        style={{ height: 420 }}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={cardNodeTypes}
          edgeTypes={pipeEdgeTypes}
          onNodeClick={onNodeClick}
          nodesDraggable={false}
          nodesConnectable={false}
          onlyRenderVisibleElements={false}
          panOnDrag={false}
          zoomOnScroll={false}
          zoomOnPinch={false}
          zoomOnDoubleClick={false}
          fitView
        />
      </div>
      {selected !== null ? (
        <div className="w-full min-w-0 xl:w-80">
          <h2 className="mb-2 text-sm font-semibold text-gray-700">{selected.name}</h2>
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr>
                <th className="border-b border-gray-300 px-2 py-1 text-left font-semibold text-gray-500">
                  Name
                </th>
                <th className="border-b border-gray-300 px-2 py-1 text-left font-semibold text-gray-500">
                  Value
                </th>
              </tr>
            </thead>
            <tbody>
              {selected.init_params.map((param) => (
                <tr key={param.name} className="border-b border-gray-100">
                  <td className="px-2 py-1 text-gray-700">{param.name}</td>
                  <td className="px-2 py-1 text-gray-700">{param.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  )
}
