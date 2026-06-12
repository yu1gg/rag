import { request } from './http'
import type {
  ApiEnvelope,
  QaPayload,
  QaResult,
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



