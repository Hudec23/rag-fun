// Aliases over the generated contract types (schema.d.ts is generated — never edit it).
import type { components } from './schema'

type S = components['schemas']

export type ErrorBody = S['ErrorBody']
export type Batch = S['Batch']
export type FileItem = S['File']
export type BatchWithFiles = S['BatchWithFiles']
export type BatchList = S['BatchList']
export type FileList = S['FileList']
export type Collection = S['Collection']
export type CollectionCreate = S['CollectionCreate']
export type CollectionList = S['CollectionList']
export type StageRun = S['StageRun']
export type StageRunList = S['StageRunList']
export type IngestRun = S['IngestRun']
export type QueryRun = S['QueryRun']
export type IngestParamsAll = S['IngestParamsAll']
export type ParseParams = S['ParseParams']
export type ChunkParams = S['ChunkParams']
export type EmbedParams = S['EmbedParams']
export type TransformParams = S['TransformParams']
export type RetrieveParams = S['RetrieveParams']
export type RerankParams = S['RerankParams']
export type GenerateParams = S['GenerateParams']
export type PayloadFilter = S['PayloadFilter']
export type FilterCondition = S['FilterCondition']
export type QdrantInfo = S['QdrantInfo']
export type ScrollRequest = S['ScrollRequest']
export type ScrollResponse = S['ScrollResponse']
export type QdrantPoint = S['QdrantPoint']
export type FacetResponse = S['FacetResponse']
export type Settings = S['Settings']
export type SettingsUpdate = S['SettingsUpdate']
export type TestConnectionResult = S['TestConnectionResult']
export type ModelCatalog = S['ModelCatalog']
export type Status = S['Status']
export type PipelineGraph = S['PipelineGraph']
export type Hit = S['Hit']
export type ParseArtifact = S['ParseArtifact']
export type ChunkArtifact = S['ChunkArtifact']
export type EmbedArtifact = S['EmbedArtifact']
export type StoreArtifact = S['StoreArtifact']
export type TransformArtifact = S['TransformArtifact']
export type RetrieveArtifact = S['RetrieveArtifact']
export type RerankArtifact = S['RerankArtifact']
export type GenerateArtifact = S['GenerateArtifact']

export type IngestStage = 'parse' | 'chunk' | 'embed' | 'store'
export type QueryStage = 'transform' | 'retrieve' | 'rerank' | 'generate'
export type Stage = IngestStage | QueryStage

// SSE events (contracts/events/*.schema.json)
export type RunEvent =
  | {
      type: 'stage.started'
      run_id: string
      stage_run_id: string
      stage: Stage
      version: number
      ts: string
    }
  | {
      type: 'stage.progress'
      run_id: string
      stage_run_id: string
      stage: Stage
      version: number
      ts: string
      done: number
      total: number
      message: string
    }
  | {
      type: 'stage.completed'
      run_id: string
      stage_run_id: string
      stage: Stage
      version: number
      ts: string
      artifact_key: string
      summary: Record<string, unknown>
    }
  | {
      type: 'stage.failed'
      run_id: string
      stage_run_id: string
      stage: Stage
      version: number
      ts: string
      error: ErrorBody
    }
  | {
      type: 'generate.token'
      run_id: string
      stage_run_id: string
      stage: 'generate'
      version: number
      ts: string
      index: number
      text: string
    }
  | {
      type: 'run.updated'
      run_id: string
      run_kind: 'ingest' | 'query'
      reason: string
      ts: string
    }
