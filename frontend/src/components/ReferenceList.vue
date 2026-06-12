<template>
  <div v-if="items.length" class="reference-list">
    <article
      v-for="item in items"
      :key="`${item.chunk_id}-${item.index}`"
      class="reference-card"
    >
      <div class="reference-meta">
        <span class="reference-badge">#{{ item.index }}</span>
        <span>chunk: {{ item.chunk_id }}</span>
        <span>doc: {{ item.doc_id }}</span>
        <span>score: {{ item.score.toFixed(4) }}</span>
      </div>
      <p class="reference-excerpt">{{ item.excerpt }}</p>
    </article>
  </div>
  <p v-else class="empty-state">{{ emptyText }}</p>
</template>

<script setup lang="ts">
import type { ReferenceItem } from '../types/api'

defineProps<{
  items: ReferenceItem[]
  emptyText: string
}>()
</script>
