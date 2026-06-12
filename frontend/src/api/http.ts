import type { ApiEnvelope } from '../types/api'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8050/api/v1'

export async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<ApiEnvelope<T>> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      signal: AbortSignal.timeout(30000),
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers ?? {}),
      },
      ...init,
    })
  } catch (err) {
    throw new Error('网络连接失败，请检查后端服务是否启动。')
  }

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

export async function* requestStream(
  path: string,
  init?: RequestInit,
): AsyncGenerator<string, void, undefined> {
  const url = `${API_BASE_URL}${path}`
  let response: Response
  try {
    response = await fetch(url, {
      signal: AbortSignal.timeout(120000),
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers as Record<string, string> | undefined),
      },
    })
  } catch (err) {
    throw new Error('网络连接失败，请检查后端服务是否启动。')
  }

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `请求失败（HTTP ${response.status}）`)
  }

  if (!response.body) {
    throw new Error('服务不支持流式响应')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') return
          yield data
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
