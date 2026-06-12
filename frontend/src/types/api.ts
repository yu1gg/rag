export interface ApiEnvelope<T> {
  code: number
  message: string
  data: T | null
}

export interface ReferenceItem {
  index: number
  chunk_id: string
  doc_id: string
  score: number
  excerpt: string
}

export interface QaPayload {
  question: string
  top_k?: number
  temperature?: number
  method?: 'vector' | 'keyword'
}

export interface QaResult {
  answer: string
  references: ReferenceItem[]
}

export interface SummaryPayload {
  text: string
  temperature?: number
}

export interface SummaryResult {
  summary: string
}

export interface HealthResult {
  status: string
  version: string
  index_ready: boolean
}

export interface IndexStatusResult {
  index_ready: boolean
  vector_count: number
  metadata_count: number
}

export interface DatasetStatsResult {
  documents_count: number
  qa_pairs_count: number
  chunks_count: number
  total_document_chars: number
}
