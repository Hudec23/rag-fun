import { apiFetch } from './client'
import type { PipelineGraph, Status } from './types'

export function getStatus(): Promise<Status> {
  return apiFetch<Status>('/status')
}

/** GET /pipeline-graphs → items. */
export function listPipelineGraphs(): Promise<PipelineGraph[]> {
  return apiFetch<{ items: PipelineGraph[] }>('/pipeline-graphs').then((r) => r.items)
}

export function getPipelineGraph(stage: string, variant: string): Promise<PipelineGraph> {
  return apiFetch<PipelineGraph>(`/pipeline-graphs/${stage}/${variant}`)
}
