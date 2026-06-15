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
        <div class="reference-id">chunk: {{ item.chunk_id }}</div>
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

.reference-id {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--muted);
}
</style>
