import { request } from './http'
import type {
  ApiEnvelope,
  QaPayload,
  QaResult,
  SearchPayload,
  SearchResult,
  SummaryPayload,
  SummaryResult,
} from '../types/api'

export function fetchQa(payload: QaPayload): Promise<ApiEnvelope<QaResult>> {
  return request<QaResult>('/rag/qa', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function fetchSummary(
  payload: SummaryPayload,
): Promise<ApiEnvelope<SummaryResult>> {
  return request<SummaryResult>('/rag/summary', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function fetchSearch(
  payload: SearchPayload,
): Promise<ApiEnvelope<SearchResult>> {
  return request<SearchResult>('/rag/search', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

