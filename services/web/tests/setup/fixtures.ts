// Contract example data shared by web tests (valid against contracts/, see tests/contract_fixtures).
import type { Collection } from '../../src/api/types'

export const COLLECTION: Collection = {
  id: '019a4b2c-1d00-7b00-8000-0000000000aa',
  name: 'default',
  qdrant_name: 'rf_019a4b2c1d007b0080000000000000aa',
  dense_model: 'bge-m3',
  dense_dims: 1024,
  sparse_model: 'Qdrant/bm25',
  created_at: '2026-11-01T18:22:05.123Z',
}

import chunkJson from '../../../../tests/contract_fixtures/artifact_chunk.json'
import embedJson from '../../../../tests/contract_fixtures/artifact_embed.json'
import generateJson from '../../../../tests/contract_fixtures/artifact_generate.json'
import parseJson from '../../../../tests/contract_fixtures/artifact_parse.json'
import rerankJson from '../../../../tests/contract_fixtures/artifact_rerank.json'
import retrieveJson from '../../../../tests/contract_fixtures/artifact_retrieve.json'
import storeJson from '../../../../tests/contract_fixtures/artifact_store.json'
import transformJson from '../../../../tests/contract_fixtures/artifact_transform.json'
import graphJson from '../../../../tests/contract_fixtures/shared__pipeline-graph.json'
import type {
  ChunkArtifact,
  EmbedArtifact,
  GenerateArtifact,
  ParseArtifact,
  PipelineGraph,
  RerankArtifact,
  RetrieveArtifact,
  StageRun,
  StoreArtifact,
  TransformArtifact,
} from '../../src/api/types'

export const PARSE = parseJson as unknown as ParseArtifact
export const CHUNK = chunkJson as unknown as ChunkArtifact
export const EMBED = embedJson as unknown as EmbedArtifact
export const STORE = storeJson as unknown as StoreArtifact
export const TRANSFORM = transformJson as unknown as TransformArtifact
export const RETRIEVE = retrieveJson as unknown as RetrieveArtifact
export const RERANK = rerankJson as unknown as RerankArtifact
export const GENERATE = generateJson as unknown as GenerateArtifact
export const GRAPH = graphJson as unknown as PipelineGraph

export const RUN_ID = '019a4b2c-2000-7c00-9000-000000000002'
export const FILE_ID = '019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a01'

export function stageRun(stage: StageRun['stage'], over: Partial<StageRun> = {}): StageRun {
  return {
    id: `019a4b2c-21${String(['parse', 'chunk', 'embed', 'store', 'transform', 'retrieve', 'rerank', 'generate'].indexOf(stage)).padStart(2, '0')}-7c00-9000-000000000003`,
    run_id: RUN_ID,
    run_kind: ['parse', 'chunk', 'embed', 'store'].includes(stage) ? 'ingest' : 'query',
    stage,
    version: 1,
    params: {},
    status: 'done',
    artifact_key: `${RUN_ID}/${stage}/v1.json`,
    summary: null,
    error: null,
    created_at: '2026-11-01T18:22:05.123Z',
    started_at: '2026-11-01T18:22:05.123Z',
    finished_at: '2026-11-01T18:22:06.123Z',
    ...over,
  }
}
