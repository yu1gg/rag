import { request } from './http'
import type {
  ApiEnvelope,
  DatasetStatsResult,
  HealthResult,
  IndexStatusResult,
} from '../types/api'

export function fetchHealth(): Promise<ApiEnvelope<HealthResult>> {
  return request<HealthResult>('/health')
}

export function fetchIndexStatus(): Promise<ApiEnvelope<IndexStatusResult>> {
  return request<IndexStatusResult>('/index/status')
}

export function fetchDatasetStats(): Promise<ApiEnvelope<DatasetStatsResult>> {
  return request<DatasetStatsResult>('/datasets/stats')
}
