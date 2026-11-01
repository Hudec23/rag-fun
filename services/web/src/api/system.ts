import type { PipelineGraph, Status } from './types'

export function getStatus(): Promise<Status> {
  throw new Error('not implemented')
}

/** GET /pipeline-graphs → items. */
export function listPipelineGraphs(): Promise<PipelineGraph[]> {
  throw new Error('not implemented')
}

export function getPipelineGraph(_stage: string, _variant: string): Promise<PipelineGraph> {
  throw new Error('not implemented')
}
