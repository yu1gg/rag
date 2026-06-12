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
        <div class="workspace-header__lead">
          <button
            class="ghost-button ghost-button--mobile"
            type="button"
            @click="mobileSessionsOpen = !mobileSessionsOpen"
          >
            {{ mobileSessionsOpen ? '收起会话' : '打开会话' }}
          </button>
          <p class="eyebrow">{{ appTitle }}</p>
          <h1>聊天式 RAG 工作台</h1>
          <p class="workspace-subtitle">
            前端已成为主要人工交互入口。你可以在同一会话里切换问答和摘要。
          </p>
        </div>

        <div class="workspace-header__actions">
          <RouterLink class="header-link" to="/">主页</RouterLink>
          <a class="header-link" :href="docsUrl" target="_blank" rel="noreferrer">
            接口调试
          </a>
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
            ]"
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
      <section class="info-card">
        <div class="info-card__header">
          <div>
            <p class="section-tag">Signals</p>
            <h2>系统状态</h2>
          </div>
          <button class="ghost-button" type="button" @click="refreshStatus" :disabled="statusLoading">
            {{ statusLoading ? '刷新中...' : '刷新' }}
          </button>
        </div>

        <div class="status-stack">
          <article class="status-panel">
            <div class="status-panel__head">
              <h3>Health</h3>
              <span v-if="healthState.data" class="status-dot" :class="{ 'status-dot--ok': healthState.data.index_ready }"></span>
            </div>
            <p v-if="healthState.error" class="status-panel__error">{{ healthState.error }}</p>
            <template v-else-if="healthState.data">
              <p>status: {{ healthState.data.status }}</p>
              <p>version: {{ healthState.data.version }}</p>
              <p>index_ready: {{ healthState.data.index_ready ? 'true' : 'false' }}</p>
            </template>
            <p v-else class="empty-state">等待加载状态信息。</p>
          </article>

          <article class="status-panel">
            <div class="status-panel__head">
              <h3>Index</h3>
              <span
                v-if="indexState.data"
                class="status-dot"
                :class="{ 'status-dot--ok': indexState.data.index_ready }"
              ></span>
            </div>
            <p v-if="indexState.error" class="status-panel__error">{{ indexState.error }}</p>
            <template v-else-if="indexState.data">
              <p>vector_count: {{ indexState.data.vector_count }}</p>
              <p>metadata_count: {{ indexState.data.metadata_count }}</p>
            </template>
            <p v-else class="empty-state">等待加载索引状态。</p>
          </article>

          <article class="status-panel">
            <div class="status-panel__head">
              <h3>Dataset</h3>
              <span v-if="datasetState.data" class="status-dot status-dot--ok"></span>
            </div>
            <p v-if="datasetState.error" class="status-panel__error">{{ datasetState.error }}</p>
            <template v-else-if="datasetState.data">
              <p>documents: {{ datasetState.data.documents_count }}</p>
              <p>qa_pairs: {{ datasetState.data.qa_pairs_count }}</p>
              <p>chunks: {{ datasetState.data.chunks_count }}</p>
            </template>
            <p v-else class="empty-state">等待加载数据集统计。</p>
          </article>
        </div>
      </section>

      <section class="info-card">
        <div class="info-card__header">
          <div>
            <p class="section-tag">Detail</p>
            <h2>当前结果详情</h2>
          </div>
        </div>

        <div v-if="latestAssistantMessage" class="detail-block">
          <div class="detail-block__meta">
            <span class="mode-badge">{{ modeLabelMap[latestAssistantMessage.mode] }}</span>
            <span>{{ latestAssistantMessage.status === 'error' ? '错误' : latestAssistantMessage.status === 'loading' ? '处理中' : '已完成' }}</span>
            <time>{{ formatTime(latestAssistantMessage.createdAt) }}</time>
          </div>

          <template v-if="latestAssistantMessage.mode === 'summary'">
            <div class="summary-stats">
              <article>
                <span>输入长度</span>
                <strong>{{ latestAssistantMessage.meta.inputLength ?? 0 }}</strong>
              </article>
              <article>
                <span>摘要长度</span>
                <strong>{{ latestAssistantMessage.meta.outputLength ?? 0 }}</strong>
              </article>
            </div>
            <p class="detail-note">
              Summary 模式不会展示 references，右侧只保留长度统计和模式说明。
            </p>
          </template>

          <template v-else>
            <p class="detail-note">
              QA 模式展示用于生成答案的参考片段。
            </p>
            <ReferenceList
              :items="latestAssistantMessage.meta.references ?? []"
              :empty-text="latestAssistantMessage.status === 'loading'
                ? '正在等待后端返回参考片段。'
                : '当前结果没有可展示的参考片段。'"
            />
          </template>
        </div>

        <p v-else class="empty-state">
          还没有助手结果。发送第一条消息后，这里会跟随显示最新结果的详情。
        </p>
      </section>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { getErrorMessage } from '../api/error'
import { fetchQa, fetchSummary } from '../api/rag'
import { fetchDatasetStats, fetchHealth, fetchIndexStatus } from '../api/state'
import ReferenceList from '../components/ReferenceList.vue'
import { appTitle } from '../stores/app'
import { useChatWorkspace } from '../stores/chatWorkspace'
import type {
  DatasetStatsResult,
  HealthResult,
  IndexStatusResult,
  QaPayload,
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

const latestAssistantMessage = computed<ChatMessage | null>(() => {
  const messages = activeSession.value?.messages ?? []
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

  return {
    question,
    top_k: topK.value,
    temperature: temperature.value,
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

  isSubmitting.value = true

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

  try {
    if (currentMode.value === 'qa') {
      const response = await fetchQa(payload as QaPayload)
      const answer = response.data?.answer?.trim() ?? ''
      const references = response.data?.references ?? []
      updateMessage(session.id, pendingMessage.id, {
        text: answer || '问答接口已返回，但答案为空。',
        status: 'success',
        meta: {
          references,
          query: (payload as QaPayload).question,
          topK: (payload as QaPayload).top_k,
          temperature: (payload as QaPayload).temperature,
        },
      })
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

    draft.value = ''
  } catch (error) {
    updateMessage(session.id, pendingMessage.id, {
      text: getErrorMessage(error),
      status: 'error',
      meta: {},
    })
    draft.value = rawInput
  } finally {
    isSubmitting.value = false
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
