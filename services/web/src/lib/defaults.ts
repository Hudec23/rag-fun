// Default params per stage/strategy = contracts/shared/common.schema.json defaults.
import type {
  ChunkParams,
  EmbedParams,
  GenerateParams,
  IngestParamsAll,
  ParseParams,
  RerankParams,
  RetrieveParams,
  TransformParams,
} from '../api/types'

export const PARSE_DEFAULTS: Record<'docling_layout' | 'docling_ocr' | 'plain_text', ParseParams> =
  {
    docling_layout: { strategy: 'docling_layout', extract_tables: true, page_images: true },
    docling_ocr: { strategy: 'docling_ocr', extract_tables: true, page_images: true },
    plain_text: { strategy: 'plain_text' },
  }

export const CHUNK_DEFAULTS: Record<
  'fixed' | 'sentence' | 'recursive' | 'semantic' | 'structure' | 'table',
  ChunkParams
> = {
  fixed: { strategy: 'fixed', split_by: 'word', length: 200, overlap: 20 },
  sentence: { strategy: 'sentence', length: 5, overlap: 1 },
  recursive: {
    strategy: 'recursive',
    length: 1000,
    overlap: 100,
    separators: ['\n\n', 'sentence', '\n', ' '],
  },
  semantic: {
    strategy: 'semantic',
    breakpoint_percentile: 90,
    min_sentences: 2,
    max_sentences: 20,
  },
  structure: { strategy: 'structure', max_tokens: 512, merge_peers: true },
  table: { strategy: 'table', row_chunks: false, text_length: 1000, text_overlap: 100 },
}

export const EMBED_DEFAULTS: EmbedParams = { batch_size: 16 }
export const TRANSFORM_DEFAULTS: TransformParams = { strategy: 'none', num_queries: 3 }
export const RETRIEVE_DEFAULTS: RetrieveParams = {
  mode: 'hybrid',
  top_k: 10,
  rrf_k: 60,
  filters: {},
}
export const RERANK_DEFAULTS: RerankParams = { enabled: true, top_n: 5 }
export const GENERATE_DEFAULTS: GenerateParams = {
  max_context_tokens: 4000,
  temperature: 0.2,
  max_answer_tokens: 800,
}

export const INGEST_DEFAULTS: IngestParamsAll = {
  parse: PARSE_DEFAULTS.docling_layout,
  chunk: CHUNK_DEFAULTS.recursive,
  embed: EMBED_DEFAULTS,
  store: {},
}
