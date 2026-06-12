<template>
  <section class="page-card page-card--interactive">
    <p class="section-tag">Summary</p>
    <h2>文本摘要</h2>
    <p>输入待处理文本后可直接请求摘要服务，适合验证模型在长文本压缩场景下的输出效果。</p>

    <form class="tool-form" @submit.prevent="handleSubmit">
      <label class="field">
        <span>原文内容</span>
        <textarea
          v-model="text"
          class="field-textarea field-textarea--large"
          rows="10"
          placeholder="粘贴需要摘要的原文内容，支持多段文本。"
        />
        <small>当前已输入 {{ trimmedLength }} 个字符。</small>
      </label>

      <div class="form-grid form-grid--single">
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
          <small>范围 0-1.5，值越高摘要表达越自由。</small>
        </label>
      </div>

      <p class="inline-note">
        当前页面是主要人工入口；需要排查接口问题时，可转到后端 <code>/docs</code> 查看原始请求。
      </p>

      <p v-if="errorMessage" class="status-banner status-banner--error">
        {{ errorMessage }}
      </p>
      <p v-else-if="isLoading" class="status-banner status-banner--info">
        正在生成摘要，请稍候...
      </p>

      <div class="action-row">
        <button class="primary-button" type="submit" :disabled="isLoading">
          {{ isLoading ? '摘要中...' : '生成摘要' }}
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

    <article class="result-panel">
      <p class="result-label">摘要结果</p>
      <p v-if="summary" class="result-text">{{ summary }}</p>
      <p v-else class="empty-state">提交原文后，这里会显示摘要结果。</p>
    </article>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

import { getErrorMessage } from '../api/error'
import { fetchSummary } from '../api/rag'
import type { SummaryPayload } from '../types/api'

const text = ref('')
const temperature = ref(0.5)
const summary = ref('')
const errorMessage = ref('')
const isLoading = ref(false)

const trimmedLength = computed(() => text.value.trim().length)

function buildPayload(): SummaryPayload | null {
  const trimmedText = text.value.trim()
  if (!trimmedText) {
    errorMessage.value = '请输入原文内容后再提交。'
    return null
  }

  if (!Number.isFinite(temperature.value) || temperature.value < 0 || temperature.value > 1.5) {
    errorMessage.value = 'Temperature 必须在 0 到 1.5 之间。'
    return null
  }

  return {
    text: trimmedText,
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
  summary.value = ''

  try {
    const response = await fetchSummary(payload)
    summary.value = response.data?.summary?.trim() ?? ''
  } catch (error) {
    errorMessage.value = getErrorMessage(error)
  } finally {
    isLoading.value = false
  }
}

function resetForm() {
  text.value = ''
  temperature.value = 0.5
  summary.value = ''
  errorMessage.value = ''
}
</script>
