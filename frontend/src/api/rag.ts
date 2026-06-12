import { request, requestStream } from './http'
import type {
  ApiEnvelope,
  QaPayload,
  QaResult,
  QaStreamEvent,
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

export async function* fetchQaStream(
  payload: QaPayload,
): AsyncGenerator<QaStreamEvent, void, undefined> {
  const stream = requestStream('/rag/qa/stream', {
    method: 'POST',
    body: JSON.stringify(payload),
  })

  for await (const line of stream) {
    yield JSON.parse(line) as QaStreamEvent
  }
}




