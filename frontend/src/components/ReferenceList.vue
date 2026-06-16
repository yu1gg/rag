<template>
  <div v-if="items.length" class="reference-list">
    <article
      v-for="item in items"
      :key="item.chunk_id"
      class="reference-card"
    >
      <div class="reference-card__dot"></div>
      <div class="reference-card__body">
        <div class="reference-meta">
          <span class="reference-badge">{{ item.index }}</span>
          <span class="reference-score">{{ (item.score * 100).toFixed(0) }}%</span>
        </div>
        <p class="reference-excerpt">{{ item.excerpt }}</p>
        <div class="reference-source">
          <span v-if="item.doc_title" class="reference-source__title">{{ item.doc_title }}</span>
          <span class="reference-source__meta">
            <span v-if="item.source">{{ item.source }}</span>
            <span v-if="item.date"> · {{ item.date }}</span>
            <a
              v-if="item.url"
              :href="item.url"
              target="_blank"
              rel="noopener noreferrer"
              class="reference-source__link"
            >&nearr; 查看原文</a>
          </span>
        </div>
      </div>
    </article>
  </div>
  <p v-else class="empty-state">{{ emptyText }}</p>
</template>

<script setup lang="ts">
import type { ReferenceItem } from '../../types/api'

defineProps<{
  items: ReferenceItem[]
  emptyText: string
}>()
</script>

<style scoped>
.reference-list {
  display: grid;
  gap: 12px;
}

.reference-card {
  display: flex;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--graphite);
  border-radius: 6px;
  transition: border-color 0.15s;
}

.reference-card:hover {
  border-color: var(--cinnabar);
}

.reference-card__dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  background: var(--cinnabar);
  flex-shrink: 0;
  margin-top: 4px;
}

.reference-card__body {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.reference-meta {
  display: flex;
  gap: 8px;
  align-items: center;
}

.reference-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px; height: 22px;
  border-radius: 50%;
  background: var(--ink);
  color: white;
  font-size: 0.72rem;
  font-weight: 600;
}

.reference-score {
  font-size: 0.78rem;
  color: var(--muted);
}

.reference-excerpt {
  font-size: 0.85rem;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--ink);
}

.reference-source {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--graphite);
  display: grid;
  gap: 4px;
}

.reference-source__title {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--ink);
  line-height: 1.4;
}

.reference-source__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 0.75rem;
  color: var(--muted);
}

.reference-source__link {
  color: var(--cinnabar);
  text-decoration: none;
  font-weight: 500;
}
.reference-source__link:hover {
  text-decoration: underline;
}
</style>
