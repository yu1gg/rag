import type { ApiEnvelope } from '../types/api'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8050/api/v1'

export async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<ApiEnvelope<T>> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  const rawText = await response.text()
  let payload: ApiEnvelope<T> | null = null

  if (rawText) {
    try {
      payload = JSON.parse(rawText) as ApiEnvelope<T>
    } catch {
      if (response.ok) {
        throw new Error('服务返回了无法解析的响应。')
      }
      throw new Error(`请求失败（HTTP ${response.status}），且响应不是有效 JSON。`)
    }
  }

  if (!response.ok) {
    throw new Error(payload?.message?.trim() || `请求失败（HTTP ${response.status}）`)
  }
  if (!payload) {
    throw new Error('服务返回了空响应。')
  }
  return payload
}
