<template>
  <div class="workspace-shell">
    <aside
      class="workspace-sidebar"
      :class="{ 'workspace-sidebar--open': mobileSessionsOpen }"
    >
      <div class="sidebar-head">
        <div>
          <p class="eyebrow">Workspace</p>
          <h2>本地会话</h2>
        </div>
        <button class="ghost-button" type="button" @click="handleNewSession">
          新对话
        </button>
      </div>

      <p class="sidebar-note">最近 20 个会话会自动保存在当前浏览器。</p>

      <div class="session-list">
        <button
          v-for="session in sessions"
          :key="session.id"
          class="session-item"
          :class="{ 'session-item--active': session.id === activeSessionId }"
          type="button"
          @click="handleSelectSession(session.id)"
        >
          <div class="session-item__body">
            <div class="session-item__meta">
              <span class="mode-badge mode-badge--muted">
                {{ modeLabelMap[session.lastMode] }}
              </span>
              <time>{{ formatTime(session.updatedAt) }}</time>
            </div>
            <strong>{{ session.title }}</strong>
            <p>{{ buildSessionPreview(session) }}</p>
          </div>
          <span
            class="session-item__delete"
            title="删除会话"
            @click.stop="handleDeleteSession(session.id)"
          >
            ×
          </span>
        </button>
      </div>
    </aside>

    <section class="workspace-main">
      <header class="workspace-header">
        <button
          class="ghost-button ghost-button--mobile"
          type="button"
          @click="mobileSessionsOpen = !mobileSessionsOpen"
        >
          {{ mobileSessionsOpen ? '收起会话' : '打开会话' }}
        </button>
        <h1 class="workspace-header__title">project_X</h1>

        <div class="workspace-header__center">
          <PipelineIndicator
            :stage="pipelineStage"
            :active="isSubmitting"
          />
        </div>

        <div class="workspace-header__actions">
          <div class="mode-switcher">
            <button
              v-for="mode in modes"
              :key="mode"
              class="mode-switcher__button"
              :class="{ 'mode-switcher__button--active': currentMode === mode }"
              @click="handleModeSwitch(mode)"
            >
              {{ modeLabelMap[mode] }}
            </button>
          </div>
          <a class="header-link" :href="docsUrl" target="_blank" rel="noreferrer">API</a>
        </div>
      </header>

      <div class="chat-stage">
        <div v-if="!activeSession?.messages.length" class="welcome-panel">
          <p class="section-tag">Start Here</p>
          <h2>默认是聊天界面，不再是工具表单页</h2>
          <p>
            输入框上方可以切换 <code>QA</code> 和 <code>Summary</code>
            两种模式。当前模式决定这次发送会调用哪个后端接口。
          </p>

          <div class="welcome-grid">
            <article>
              <h3>QA</h3>
              <p>适合知识问答，主区展示答案，右侧展示参考片段。</p>
            </article>
            <article>
              <h3>Summary</h3>
              <p>适合长文本压缩，右侧展示输入/输出长度和模式说明。</p>
            </article>
          </div>
        </div>

        <div v-else ref="messageListRef" class="message-list">
          <article
            v-for="message in activeSession.messages"
            :key="message.id"
            class="chat-message"
            :class="[
              `chat-message--${message.role}`,
              `chat-message--${message.status}`,
              { 'chat-message--selected': message.id === selectedMessageId },
            ]"
            @click="selectedMessageId = message.id"
          >
            <div class="chat-message__meta">
              <span>{{ message.role === 'user' ? '你' : '助手' }}</span>
              <span class="mode-badge">{{ modeLabelMap[message.mode] }}</span>
              <time>{{ formatTime(message.createdAt) }}</time>
            </div>

            <div class="chat-message__bubble">
              <p>{{ message.text }}</p>
              <div
                v-if="message.status === 'loading'"
                class="chat-message__loading"
                aria-label="loading"
              >
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </article>
        </div>
      </div>

      <form class="composer" @submit.prevent="handleSubmit">
        <div class="mode-switcher">
          <button
            v-for="mode in modes"
            :key="mode"
            class="mode-switcher__button"
            :class="{ 'mode-switcher__button--active': currentMode === mode }"
            type="button"
            @click="handleModeSwitch(mode)"
          >
            {{ modeLabelMap[mode] }}
          </button>
        </div>

        <div v-if="currentMode === 'qa'" class="retrieval-switcher">
          <span class="retrieval-switcher__label">检索方法</span>
          <button
            class="retrieval-switcher__button"
            :class="{ 'retrieval-switcher__button--active': retrievalMethod === 'vector' }"
            type="button"
            @click="retrievalMethod = 'vector'"
          >
            向量检索
          </button>
          <button
            class="retrieval-switcher__button"
            :class="{ 'retrieval-switcher__button--active': retrievalMethod === 'keyword' }"
            type="button"
            @click="retrievalMethod = 'keyword'"
          >
            关键词检索
          </button>
        </div>

        <div class="composer-toolbar">
          <label v-if="currentMode !== 'summary'" class="compact-field">
            <span>Top-K</span>
            <input
              v-model.number="topK"
              type="number"
              min="1"
              max="10"
              step="1"
            />
          </label>

          <label class="compact-field">
            <span>Temperature</span>
            <input
              v-model.number="temperature"
              type="number"
              min="0"
              max="1.5"
              step="0.1"
            />
          </label>

          <p class="composer-toolbar__hint">
            {{ modeHints[currentMode] }}
          </p>
        </div>

        <p v-if="validationError" class="composer-error">{{ validationError }}</p>

        <div class="composer-box">
          <textarea
            v-model="draft"
            class="composer-box__input"
            :placeholder="placeholderMap[currentMode]"
            :disabled="isSubmitting"
            rows="4"
            @keydown="handleKeydown"
          />
          <button class="primary-button" type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? '发送中...' : '发送' }}
          </button>
        </div>

        <p class="composer-footnote">
          Enter 发送，Shift + Enter 换行。接口异常会显示为助手消息，不会弹窗打断。
        </p>
      </form>
    </section>

    <aside class="workspace-info">
      <div>
        <h2>批注来源</h2>
        <p class="info-subtitle">
          {{ selectedDetailMessage ? '点击消息的回看详情' : '最新回答的参考来源' }}
        </p>
      </div>

      <div v-if="selectedDetailMessage" class="detail-block">
        <div class="detail-block__meta">
          <span class="mode-badge">{{ modeLabelMap[selectedDetailMessage.mode] }}</span>
          <time>{{ formatTime(selectedDetailMessage.createdAt) }}</time>
        </div>

        <template v-if="selectedDetailMessage.mode === 'summary'">
          <div class="summary-stats">
            <div class="summary-stat">
              <span class="summary-stat__label">原文长度</span>
              <strong>{{ selectedDetailMessage.meta.inputLength ?? 0 }}</strong>
            </div>
            <div class="summary-stat">
              <span class="summary-stat__label">摘要长度</span>
              <strong>{{ selectedDetailMessage.meta.outputLength ?? 0 }}</strong>
            </div>
          </div>
        </template>

        <ReferenceList
          v-else
          :items="selectedDetailMessage.meta.references ?? []"
          empty-text="该回答没有关联的参考来源。"
        />
      </div>

      <p v-else class="empty-state">
        还没有助手结果。发送第一条消息后，这里会跟随显示最新结果的批注来源。
      </p>

      <div class="system-status">
        <span class="status-dot" :class="{ 'status-dot--ok': healthState.data?.index_ready }"></span>
        <span class="system-status__label">索引就绪</span>
        <span class="status-dot" :class="{ 'status-dot--ok': indexState.data?.index_ready }" style="margin-left: 12px"></span>
        <span class="system-status__label">{{ indexState.data?.vector_count ?? 0 }} 向量</span>
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { getErrorMessage } from '../api/error'
import { fetchQaStream, fetchSummary } from '../api/rag'
import { fetchDatasetStats, fetchHealth, fetchIndexStatus } from '../api/state'
import ReferenceList from '../components/ReferenceList.vue'
import PipelineIndicator from '../components/PipelineIndicator.vue'
import { appTitle } from '../stores/app'
import { useChatWorkspace } from '../stores/chatWorkspace'
import type {
  DatasetStatsResult,
  HealthResult,
  IndexStatusResult,
  QaPayload,
  ReferenceItem,
  SummaryPayload,
} from '../types/api'
import type { ChatMessage, ChatSession, ToolMode } from '../types/chat'

type StatusSlice<T> = {
  data: T | null
  error: string
}

const modeLabelMap: Record<ToolMode, string> = {
  qa: 'QA',
  summary: 'Summary',
}

const placeholderMap: Record<ToolMode, string> = {
  qa: '例如：什么是 RAG，它为什么适合构建知识问答系统？',
  summary: '粘贴需要摘要的长文本，发送后会返回压缩结果。',
}

const modeHints: Record<ToolMode, string> = {
  qa: '问答模式会调用 /rag/qa，返回答案正文和参考片段。',
  summary: '摘要模式会调用 /rag/summary，适合整理长文本内容。',
}

const modeToRoute: Record<ToolMode, string> = {
  qa: '/qa',
  summary: '/summary',
}

const modes: ToolMode[] = ['qa', 'summary']
const retrievalMethod = ref<'vector' | 'keyword'>('vector')
const draft = ref('')
const topK = ref(5)
const temperature = ref(0.7)
const validationError = ref('')
const isSubmitting = ref(false)
const mobileSessionsOpen = ref(false)
const statusLoading = ref(false)
const messageListRef = ref<HTMLElement | null>(null)

const route = useRoute()
const router = useRouter()

const {
  sessions,
  activeSessionId,
  activeSession,
  currentMode,
  hydrateWorkspace,
  createSession,
  setCurrentMode,
  setActiveSession,
  deleteSession,
  appendMessage,
  updateMessage,
  selectedMessageId,
} = useChatWorkspace()

const healthState = reactive<StatusSlice<HealthResult>>({
  data: null,
  error: '',
})
const indexState = reactive<StatusSlice<IndexStatusResult>>({
  data: null,
  error: '',
})
const datasetState = reactive<StatusSlice<DatasetStatsResult>>({
  data: null,
  error: '',
})

const selectedDetailMessage = computed<ChatMessage | null>(() => {
  const messages = activeSession.value?.messages ?? []
  if (selectedMessageId.value) {
    return messages.find((m) => m.id === selectedMessageId.value) ?? null
  }
  // Fall back to latest assistant message
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    if (messages[index].role === 'assistant') {
      return messages[index]
    }
  }
  return null
})

const docsUrl = computed(() => {
  const apiBase = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8050/api/v1'
  return apiBase.replace(/\/api\/v1\/?$/, '/docs')
})

const pipelineStage = computed(() => {
  if (!activeSession.value?.messages.length) return 0
  const last = activeSession.value.messages[activeSession.value.messages.length - 1]
  if (last.role === 'user' || last.status === 'loading') return 1
  if (last.status === 'success') return 3
  return 0
})

function normalizeMode(value: unknown): ToolMode {
  return value === 'summary' ? value : 'qa'
}

function formatTime(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function buildSessionPreview(session: ChatSession): string {
  const lastMessage = [...session.messages].reverse().find((message) => message.role === 'user')
  if (!lastMessage) {
    return '等待第一条消息...'
  }

  const compact = lastMessage.text.trim().replace(/\s+/g, ' ')
  return compact.length > 42 ? `${compact.slice(0, 42)}...` : compact
}

function syncModeFromRoute(): void {
  const routeMode = normalizeMode(route.meta.defaultMode)
  setCurrentMode(routeMode)
}

async function scrollToBottom(): Promise<void> {
  await nextTick()
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

function handleModeSwitch(mode: ToolMode): void {
  setCurrentMode(mode)
  mobileSessionsOpen.value = false
  if (route.path !== modeToRoute[mode]) {
    void router.replace(modeToRoute[mode])
  }
}

function handleNewSession(): void {
  createSession(currentMode.value)
  draft.value = ''
  validationError.value = ''
  mobileSessionsOpen.value = false
}

function handleSelectSession(sessionId: string): void {
  const session = sessions.value.find((item) => item.id === sessionId)
  if (!session) {
    return
  }

  setActiveSession(sessionId)
  mobileSessionsOpen.value = false
  if (route.path !== modeToRoute[session.lastMode]) {
    void router.replace(modeToRoute[session.lastMode])
  }
}

function handleDeleteSession(sessionId: string): void {
  deleteSession(sessionId)
  const nextMode = activeSession.value?.lastMode ?? currentMode.value
  if (route.path !== modeToRoute[nextMode]) {
    void router.replace(modeToRoute[nextMode])
  }
}

function buildQaPayload(): QaPayload | null {
  const question = draft.value.trim()
  if (!question) {
    validationError.value = '请输入问题后再发送。'
    return null
  }
  if (!Number.isInteger(topK.value) || topK.value < 1 || topK.value > 10) {
    validationError.value = 'Top-K 必须是 1 到 10 之间的整数。'
    return null
  }
  if (!Number.isFinite(temperature.value) || temperature.value < 0 || temperature.value > 1.5) {
    validationError.value = 'Temperature 必须在 0 到 1.5 之间。'
    return null
  }

  // Build history from current session's last messages (up to 6 turns)
  const session = activeSession.value
  const history: { role: 'user' | 'assistant'; content: string }[] = []
  if (session) {
    const recentMessages = session.messages.slice(-6)
    for (const msg of recentMessages) {
      if (msg.status !== 'loading') {
        history.push({
          role: msg.role,
          content: msg.text,
        })
      }
    }
  }

  return {
    question,
    top_k: topK.value,
    temperature: temperature.value,
    method: retrievalMethod.value,
    history,
  }
}

function buildSummaryPayload(): SummaryPayload | null {
  const text = draft.value.trim()
  if (!text) {
    validationError.value = '请输入原文内容后再发送。'
    return null
  }
  if (!Number.isFinite(temperature.value) || temperature.value < 0 || temperature.value > 1.5) {
    validationError.value = 'Temperature 必须在 0 到 1.5 之间。'
    return null
  }

  return {
    text,
    temperature: temperature.value,
  }
}

async function handleSubmit(): Promise<void> {
  validationError.value = ''

  const rawInput = draft.value
  const trimmedInput = rawInput.trim()
  const session = activeSession.value ?? createSession(currentMode.value)

  const payload =
    currentMode.value === 'qa'
      ? buildQaPayload()
      : buildSummaryPayload()

  if (!payload) {
    return
  }

  appendMessage({
    role: 'user',
    mode: currentMode.value,
    text: trimmedInput,
    status: 'success',
    meta: {},
  })

  const pendingMessage = appendMessage({
    role: 'assistant',
    mode: currentMode.value,
    text: '正在处理，请稍候...',
    status: 'loading',
    meta: {},
  })

  await scrollToBottom()

  draft.value = ''
  isSubmitting.value = false

  try {
    if (currentMode.value === 'qa') {
      const qaPayload = payload as QaPayload
      let accumulatedText = ''
      let streamReferences: ReferenceItem[] = []

      for await (const event of fetchQaStream(qaPayload)) {
        if (event.type === 'chunk') {
          accumulatedText += event.text
          updateMessage(session.id, pendingMessage.id, {
            text: accumulatedText,
            status: 'success',
            meta: {
              query: qaPayload.question,
              topK: qaPayload.top_k,
              temperature: qaPayload.temperature,
              method: qaPayload.method,
            },
          })
        } else if (event.type === 'done') {
          streamReferences = event.references
          updateMessage(session.id, pendingMessage.id, {
            text: accumulatedText || '问答接口已返回，但答案为空。',
            status: 'success',
            meta: {
              references: streamReferences,
              query: qaPayload.question,
              topK: qaPayload.top_k,
              temperature: qaPayload.temperature,
              method: qaPayload.method,
            },
          })
        }
      }
    } else {
      const response = await fetchSummary(payload as SummaryPayload)
      const summary = response.data?.summary?.trim() ?? ''
      updateMessage(session.id, pendingMessage.id, {
        text: summary || '摘要接口已返回，但摘要为空。',
        status: 'success',
        meta: {
          inputLength: (payload as SummaryPayload).text.length,
          outputLength: summary.length,
          temperature: (payload as SummaryPayload).temperature,
        },
      })
    }
  } catch (error) {
    updateMessage(session.id, pendingMessage.id, {
      text: getErrorMessage(error),
      status: 'error',
      meta: {},
    })
  } finally {
    await scrollToBottom()
  }
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    if (!isSubmitting.value) {
      void handleSubmit()
    }
  }
}

async function refreshStatus(): Promise<void> {
  statusLoading.value = true

  const [healthResult, indexResult, datasetResult] = await Promise.allSettled([
    fetchHealth(),
    fetchIndexStatus(),
    fetchDatasetStats(),
  ])

  if (healthResult.status === 'fulfilled') {
    healthState.data = healthResult.value.data
    healthState.error = ''
  } else {
    healthState.data = null
    healthState.error = getErrorMessage(healthResult.reason)
  }

  if (indexResult.status === 'fulfilled') {
    indexState.data = indexResult.value.data
    indexState.error = ''
  } else {
    indexState.data = null
    indexState.error = getErrorMessage(indexResult.reason)
  }

  if (datasetResult.status === 'fulfilled') {
    datasetState.data = datasetResult.value.data
    datasetState.error = ''
  } else {
    datasetState.data = null
    datasetState.error = getErrorMessage(datasetResult.reason)
  }

  statusLoading.value = false
}

onMounted(async () => {
  hydrateWorkspace(normalizeMode(route.meta.defaultMode))
  syncModeFromRoute()
  await refreshStatus()
  await scrollToBottom()
})

watch(
  () => route.meta.defaultMode,
  async () => {
    syncModeFromRoute()
    await scrollToBottom()
  },
)

watch(
  () => activeSession.value?.id,
  async () => {
    await scrollToBottom()
  },
)

watch(
  () => activeSession.value?.messages.length,
  async () => {
    await scrollToBottom()
  },
)
</script>
