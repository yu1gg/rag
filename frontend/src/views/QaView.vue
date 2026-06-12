<template>
  <section class="page-card page-card--interactive">
    <p class="section-tag">QA</p>
    <h2>智能问答</h2>
    <p>输入问题并控制检索与生成参数，提交后会展示回答内容和对应参考片段。</p>

    <form class="tool-form" @submit.prevent="handleSubmit">
      <label class="field">
        <span>问题</span>
        <textarea
          v-model="question"
          class="field-textarea"
          rows="5"
          placeholder="例如：什么是 RAG，它为什么适合构建知识问答系统？"
        />
      </label>

      <div class="form-grid">
        <label class="field">
          <span>Top-K</span>
          <input
            v-model.number="topK"
            class="field-input"
            type="number"
            min="1"
            max="10"
            step="1"
          />
          <small>范围 1-10，决定参与回答的候选片段数。</small>
        </label>

        <label class="field">
          <span>Temperature</span>
          <input
            v-model.number="temperature"
            class="field-input"
            type="number"
            min="0"
            max="1.5"
            step="0.1"
          />
          <small>范围 0-1.5，值越高回答越发散。</small>
        </label>
      </div>

      <p class="inline-note">
        主要人工入口已切到前端页面；如需核对原始请求与响应包络，可继续使用后端 <code>/docs</code>。
      </p>

      <p v-if="errorMessage" class="status-banner status-banner--error">
        {{ errorMessage }}
      </p>
      <p v-else-if="isLoading" class="status-banner status-banner--info">
        正在生成回答，请稍候...
      </p>

      <div class="action-row">
        <button class="primary-button" type="submit" :disabled="isLoading">
          {{ isLoading ? '生成中...' : '提交问答' }}
        </button>
        <button
          class="secondary-button"
          type="button"
          :disabled="isLoading"
          @click="resetForm"
        >
          清空
        </button>
      </div>
    </form>

    <div class="result-stack">
      <article class="result-panel">
        <p class="result-label">回答结果</p>
        <p v-if="answer" class="result-text">{{ answer }}</p>
        <p v-else class="empty-state">提交问题后，这里会显示回答内容。</p>
      </article>

      <article class="result-panel">
        <p class="result-label">参考片段</p>
        <ReferenceList
          :items="references"
          empty-text="提交问题后，这里会展示检索到的参考片段。"
        />
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'

import { getErrorMessage } from '../api/error'
import { fetchQa } from '../api/rag'
import ReferenceList from '../components/ReferenceList.vue'
import type { QaPayload, ReferenceItem } from '../types/api'

const question = ref('')
const topK = ref(5)
const temperature = ref(0.7)
const answer = ref('')
const references = ref<ReferenceItem[]>([])
const errorMessage = ref('')
const isLoading = ref(false)

function buildPayload(): QaPayload | null {
  const trimmedQuestion = question.value.trim()
  if (!trimmedQuestion) {
    errorMessage.value = '请输入问题后再提交。'
    return null
  }

  if (!Number.isInteger(topK.value) || topK.value < 1 || topK.value > 10) {
    errorMessage.value = 'Top-K 必须是 1 到 10 之间的整数。'
    return null
  }

  if (!Number.isFinite(temperature.value) || temperature.value < 0 || temperature.value > 1.5) {
    errorMessage.value = 'Temperature 必须在 0 到 1.5 之间。'
    return null
  }

  return {
    question: trimmedQuestion,
    top_k: topK.value,
    temperature: temperature.value,
  }
}

async function handleSubmit() {
  errorMessage.value = ''
  const payload = buildPayload()
  if (!payload) {
    return
  }

  isLoading.value = true
  answer.value = ''
  references.value = []

  try {
    const response = await fetchQa(payload)
    answer.value = response.data?.answer?.trim() ?? ''
    references.value = response.data?.references ?? []
  } catch (error) {
    errorMessage.value = getErrorMessage(error)
  } finally {
    isLoading.value = false
  }
}

function resetForm() {
  question.value = ''
  topK.value = 5
  temperature.value = 0.7
  answer.value = ''
  references.value = []
  errorMessage.value = ''
}
</script>
