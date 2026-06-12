<template>
  <section class="page-card page-card--interactive">
    <p class="section-tag">Search</p>
    <h2>知识检索</h2>
    <p>直接查看后端检索返回的参考片段，适合验证索引质量、Top-K 参数和结果排序。</p>

    <form class="tool-form" @submit.prevent="handleSubmit">
      <label class="field">
        <span>检索问题</span>
        <textarea
          v-model="question"
          class="field-textarea"
          rows="4"
          placeholder="例如：Transformer 架构的核心特点是什么？"
        />
      </label>

      <div class="form-grid form-grid--single">
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
          <small>范围 1-10，用来控制返回的片段数量。</small>
        </label>
      </div>

      <p class="inline-note">
        当前页面用于快速检查检索结果；如需比对原始响应包络，可前往后端 <code>/docs</code>。
      </p>

      <p v-if="errorMessage" class="status-banner status-banner--error">
        {{ errorMessage }}
      </p>
      <p v-else-if="isLoading" class="status-banner status-banner--info">
        正在检索，请稍候...
      </p>

      <div class="action-row">
        <button class="primary-button" type="submit" :disabled="isLoading">
          {{ isLoading ? '检索中...' : '开始检索' }}
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
      <p class="result-label">检索结果</p>
      <p v-if="lastQuery" class="query-label">当前问题：{{ lastQuery }}</p>
      <ReferenceList
        :items="references"
        empty-text="提交检索问题后，这里会显示命中的参考片段。"
      />
    </article>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'

import { getErrorMessage } from '../api/error'
import { fetchSearch } from '../api/rag'
import ReferenceList from '../components/ReferenceList.vue'
import type { ReferenceItem, SearchPayload } from '../types/api'

const question = ref('')
const topK = ref(5)
const lastQuery = ref('')
const references = ref<ReferenceItem[]>([])
const errorMessage = ref('')
const isLoading = ref(false)

function buildPayload(): SearchPayload | null {
  const trimmedQuestion = question.value.trim()
  if (!trimmedQuestion) {
    errorMessage.value = '请输入检索问题后再提交。'
    return null
  }

  if (!Number.isInteger(topK.value) || topK.value < 1 || topK.value > 10) {
    errorMessage.value = 'Top-K 必须是 1 到 10 之间的整数。'
    return null
  }

  return {
    question: trimmedQuestion,
    top_k: topK.value,
  }
}

async function handleSubmit() {
  errorMessage.value = ''
  const payload = buildPayload()
  if (!payload) {
    return
  }

  isLoading.value = true
  lastQuery.value = payload.question
  references.value = []

  try {
    const response = await fetchSearch(payload)
    lastQuery.value = response.data?.query?.trim() || payload.question
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
  lastQuery.value = ''
  references.value = []
  errorMessage.value = ''
}
</script>
