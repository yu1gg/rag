import { computed, ref } from 'vue'

import type {
  ChatMessage,
  ChatMessageMeta,
  ChatMessageStatus,
  ChatRole,
  ChatSession,
  ToolMode,
} from '../types/chat'

interface PersistedWorkspace {
  activeSessionId: string
  sessions: ChatSession[]
}

const STORAGE_KEY = 'project-x-chat-workspace:v1'
const MAX_SESSIONS = 20

const sessions = ref<ChatSession[]>([])
const activeSessionId = ref('')
const currentMode = ref<ToolMode>('qa')
const hydrated = ref(false)

const activeSession = computed<ChatSession | null>(
  () => sessions.value.find((session) => session.id === activeSessionId.value) ?? null,
)

function nowIso(): string {
  return new Date().toISOString()
}

function createId(prefix: string): string {
  return `${prefix}_${Date.now()}_${Math.random().toString(16).slice(2, 10)}`
}

function trimSessions(items: ChatSession[]): ChatSession[] {
  return [...items]
    .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))
    .slice(0, MAX_SESSIONS)
}

function normalizeMode(value: unknown): ToolMode {
  if (value === 'summary') {
    return value
  }
  return 'qa'
}

function normalizeMessage(raw: unknown): ChatMessage | null {
  if (!raw || typeof raw !== 'object') {
    return null
  }

  const item = raw as Record<string, unknown>
  const role: ChatRole = item.role === 'assistant' ? 'assistant' : 'user'
  const status: ChatMessageStatus =
    item.status === 'loading' || item.status === 'error' ? item.status : 'success'

  return {
    id: typeof item.id === 'string' && item.id ? item.id : createId('msg'),
    role,
    mode: normalizeMode(item.mode),
    text: typeof item.text === 'string' ? item.text : '',
    status,
    createdAt:
      typeof item.createdAt === 'string' && item.createdAt ? item.createdAt : nowIso(),
    meta: item.meta && typeof item.meta === 'object' ? { ...item.meta } : {},
  }
}

function normalizeSession(raw: unknown): ChatSession | null {
  if (!raw || typeof raw !== 'object') {
    return null
  }

  const item = raw as Record<string, unknown>
  const messages = Array.isArray(item.messages)
    ? item.messages
        .map((message) => normalizeMessage(message))
        .filter((message): message is ChatMessage => message !== null)
    : []
  const createdAt =
    typeof item.createdAt === 'string' && item.createdAt ? item.createdAt : nowIso()
  const updatedAt =
    typeof item.updatedAt === 'string' && item.updatedAt ? item.updatedAt : createdAt

  return {
    id: typeof item.id === 'string' && item.id ? item.id : createId('session'),
    title: typeof item.title === 'string' && item.title.trim() ? item.title : '新对话',
    createdAt,
    updatedAt,
    lastMode: normalizeMode(item.lastMode),
    messages,
  }
}

function persistState(): void {
  if (typeof window === 'undefined') {
    return
  }

  const payload: PersistedWorkspace = {
    activeSessionId: activeSessionId.value,
    sessions: sessions.value,
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
}

function sortAndPersist(): void {
  sessions.value = trimSessions(sessions.value)
  if (!sessions.value.some((session) => session.id === activeSessionId.value)) {
    activeSessionId.value = sessions.value[0]?.id ?? ''
  }
  persistState()
}

function deriveTitle(text: string): string {
  const compact = text.trim().replace(/\s+/g, ' ')
  if (!compact) {
    return '新对话'
  }
  return compact.length > 18 ? `${compact.slice(0, 18)}...` : compact
}

function createSession(initialMode: ToolMode = currentMode.value): ChatSession {
  const timestamp = nowIso()
  const session: ChatSession = {
    id: createId('session'),
    title: '新对话',
    createdAt: timestamp,
    updatedAt: timestamp,
    lastMode: initialMode,
    messages: [],
  }

  sessions.value = trimSessions([session, ...sessions.value])
  activeSessionId.value = session.id
  currentMode.value = initialMode
  persistState()
  return session
}

function ensureActiveSession(): ChatSession {
  return activeSession.value ?? createSession(currentMode.value)
}

function hydrateWorkspace(defaultMode: ToolMode): void {
  if (hydrated.value) {
    currentMode.value = defaultMode
    if (activeSession.value) {
      activeSession.value.lastMode = defaultMode
      sortAndPersist()
    }
    return
  }

  hydrated.value = true
  currentMode.value = defaultMode

  if (typeof window === 'undefined') {
    createSession(defaultMode)
    return
  }

  try {
    const rawValue = window.localStorage.getItem(STORAGE_KEY)
    if (rawValue) {
      const parsed = JSON.parse(rawValue) as PersistedWorkspace
      const restoredSessions = Array.isArray(parsed.sessions)
        ? parsed.sessions
            .map((session) => normalizeSession(session))
            .filter((session): session is ChatSession => session !== null)
        : []

      sessions.value = trimSessions(restoredSessions)
      activeSessionId.value =
        sessions.value.find((session) => session.id === parsed.activeSessionId)?.id ??
        sessions.value[0]?.id ??
        ''
    }
  } catch {
    sessions.value = []
    activeSessionId.value = ''
  }

  if (!sessions.value.length) {
    createSession(defaultMode)
    return
  }

  const session = activeSession.value ?? sessions.value[0]
  activeSessionId.value = session.id
  currentMode.value = defaultMode
  session.lastMode = defaultMode
  sortAndPersist()
}

function setCurrentMode(mode: ToolMode): void {
  currentMode.value = mode
  const session = ensureActiveSession()
  session.lastMode = mode
  session.updatedAt = nowIso()
  sortAndPersist()
}

function setActiveSession(sessionId: string): void {
  const session = sessions.value.find((item) => item.id === sessionId)
  if (!session) {
    return
  }

  activeSessionId.value = session.id
  currentMode.value = session.lastMode
  persistState()
}

function deleteSession(sessionId: string): void {
  sessions.value = sessions.value.filter((session) => session.id !== sessionId)
  if (!sessions.value.length) {
    createSession(currentMode.value)
    return
  }

  if (activeSessionId.value === sessionId) {
    activeSessionId.value = sessions.value[0].id
    currentMode.value = sessions.value[0].lastMode
  }
  sortAndPersist()
}

function appendMessage(input: {
  role: ChatRole
  mode: ToolMode
  text: string
  status: ChatMessageStatus
  meta?: ChatMessageMeta
}): ChatMessage {
  const session = ensureActiveSession()
  const message: ChatMessage = {
    id: createId('msg'),
    role: input.role,
    mode: input.mode,
    text: input.text,
    status: input.status,
    createdAt: nowIso(),
    meta: input.meta ? { ...input.meta } : {},
  }

  session.messages = [...session.messages, message]
  session.updatedAt = message.createdAt
  session.lastMode = input.mode
  if (input.role === 'user' && session.messages.filter((item) => item.role === 'user').length === 1) {
    session.title = deriveTitle(input.text)
  }
  sortAndPersist()
  return message
}

function updateMessage(
  sessionId: string,
  messageId: string,
  patch: Partial<Pick<ChatMessage, 'text' | 'status' | 'meta'>>,
): ChatMessage | null {
  const session = sessions.value.find((item) => item.id === sessionId)
  if (!session) {
    return null
  }

  const message = session.messages.find((item) => item.id === messageId)
  if (!message) {
    return null
  }

  if (typeof patch.text === 'string') {
    message.text = patch.text
  }
  if (patch.status) {
    message.status = patch.status
  }
  if (patch.meta) {
    message.meta = { ...patch.meta }
  }

  session.updatedAt = nowIso()
  session.lastMode = message.mode
  sortAndPersist()
  return message
}

export function useChatWorkspace() {
  return {
    sessions,
    activeSessionId,
    activeSession,
    currentMode,
    hydrateWorkspace,
    createSession,
    setCurrentMode,
    setActiveSession,
    deleteSession,
    ensureActiveSession,
    appendMessage,
    updateMessage,
  }
}
