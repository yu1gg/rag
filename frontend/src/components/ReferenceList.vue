<template>
  <div v-if="items.length" class="reference-list">
    <article
      v-for="item in items"
      :key="item.chunk_id"
      class="reference-card"
      :class="{ 'reference-card--expanded': expandedId === item.chunk_id }"
      @click="expandedId = expandedId === item.chunk_id ? '' : item.chunk_id"
    >
      <div class="reference-card__bar"></div>
      <div class="reference-card__body">
        <div class="reference-meta">
          <span class="reference-badge">{{ item.index }}</span>
          <span class="reference-score">{{ (item.score * 100).toFixed(0) }}%</span>
        </div>
        <div
          class="reference-excerpt"
          :class="{ 'reference-excerpt--expanded': expandedId === item.chunk_id }"
          v-html="renderMarkdown(item.excerpt)"
        ></div>
        <div class="reference-source">
          <span v-if="item.doc_title" class="reference-source__title">{{ item.doc_title }}</span>
          <span class="reference-source__meta">
            <span v-if="item.source">{{ item.source }}</span>
            <span v-if="item.date"> · {{ item.date }}</span>
          </span>
          <a
            v-if="item.url"
            :href="item.url"
            target="_blank"
            rel="noopener noreferrer"
            class="reference-source__link"
            @click.stop
          >&nearr; 查看原文</a>
        </div>
      </div>
    </article>
  </div>
  <p v-else class="empty-state">{{ emptyText }}</p>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { marked } from 'marked'
import type { ReferenceItem } from '../../types/api'

defineProps<{
  items: ReferenceItem[]
  emptyText: string
}>()

const expandedId = ref('')

function renderMarkdown(text: string): string {
  return marked.parse(text, { breaks: true, async: false }) as string
}
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
  transition: border-color 0.15s, background 0.15s, box-shadow 0.2s;
  cursor: pointer;
}

.reference-card:hover {
  border-color: rgba(193, 41, 46, 0.4);
  background: rgba(193, 41, 46, 0.02);
}

.reference-card--expanded {
  border-color: var(--cinnabar);
  background: rgba(193, 41, 46, 0.04);
  box-shadow: 0 2px 12px rgba(193, 41, 46, 0.08);
}

.reference-card__bar {
  width: 3px;
  border-radius: 2px;
  background: var(--graphite);
  flex-shrink: 0;
  align-self: stretch;
  transition: background 0.2s, width 0.2s;
}

.reference-card:hover .reference-card__bar {
  background: rgba(193, 41, 46, 0.3);
}

.reference-card--expanded .reference-card__bar {
  width: 4px;
  background: var(--cinnabar);
}

.reference-card__body {
  display: grid;
  gap: 6px;
  min-width: 0;
  flex: 1;
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
  flex-shrink: 0;
}

.reference-score {
  font-size: 0.78rem;
  color: var(--muted);
}

.reference-excerpt {
  font-size: 0.85rem;
  line-height: 1.7;
  color: var(--ink);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  transition: max-height 0.3s ease;
}

.reference-excerpt--expanded {
  display: block;
  -webkit-line-clamp: unset;
  overflow: visible;
}

/* Markdown content inside excerpt */
.reference-excerpt :deep(p) { margin: 0 0 0.6em; line-height: 1.7; }
.reference-excerpt :deep(p:last-child) { margin-bottom: 0; }
.reference-excerpt :deep(strong) { font-weight: 600; }
.reference-excerpt :deep(em) { font-style: italic; }
.reference-excerpt :deep(code) {
  font-family: var(--font-mono);
  font-size: 0.88em;
  background: rgba(26, 26, 46, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
}
.reference-excerpt :deep(h1), .reference-excerpt :deep(h2),
.reference-excerpt :deep(h3), .reference-excerpt :deep(h4) {
  font-family: var(--font-display);
  font-size: 0.92rem;
  margin: 0.8em 0 0.4em;
}
.reference-excerpt :deep(ul), .reference-excerpt :deep(ol) {
  margin: 0.4em 0;
  padding-left: 1.4em;
  line-height: 1.7;
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
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  color: var(--cinnabar);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.82rem;
}
.reference-source__link:hover {
  text-decoration: underline;
}
</style>
