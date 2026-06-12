import type { ReferenceItem } from './api'

export type ToolMode = 'qa' | 'summary'
export type ChatRole = 'user' | 'assistant'
export type ChatMessageStatus = 'success' | 'loading' | 'error'

export interface ChatMessageMeta {
  references?: ReferenceItem[]
  inputLength?: number
  outputLength?: number
  query?: string
  topK?: number
  temperature?: number
}

export interface ChatMessage {
  id: string
  role: ChatRole
  mode: ToolMode
  text: string
  status: ChatMessageStatus
  createdAt: string
  meta: ChatMessageMeta
}

export interface ChatSession {
  id: string
  title: string
  createdAt: string
  updatedAt: string
  lastMode: ToolMode
  messages: ChatMessage[]
}
