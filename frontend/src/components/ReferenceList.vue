<template>
  <div v-if="items.length" class="reference-list">
    <article
      v-for="item in items"
      :key="item.chunk_id"
      class="reference-card"
      @click="open(item)"
    >
      <div class="reference-card__bar"></div>
      <div class="reference-card__body">
        <div class="reference-meta">
          <span class="reference-badge">{{ item.index }}</span>
          <span class="reference-score">{{ (item.score * 100).toFixed(0) }}%</span>
          <span v-if="item.doc_title" class="reference-card__doctitle">{{ item.doc_title }}</span>
        </div>
        <p class="reference-card__excerpt">{{ item.excerpt }}</p>
        <span v-if="item.source" class="reference-card__source-tag">{{ item.source }}</span>
      </div>
    </article>

    <!-- Pop-out modal -->
    <Teleport to="body">
      <Transition name="popout">
        <div v-if="activeItem" class="popout-overlay" @click.self="close">
          <article class="popout-card">
            <button class="popout-card__close" @click="close" aria-label="关闭">×</button>

            <div class="popout-card__meta">
              <span class="reference-badge">{{ activeItem.index }}</span>
              <span class="reference-score">{{ (activeItem.score * 100).toFixed(0) }}%</span>
            </div>

            <div
              class="popout-card__content"
              v-html="renderMarkdown(activeItem.full_content || activeItem.excerpt)"
            ></div>

            <div class="popout-card__footer">
              <div v-if="activeItem.doc_title" class="popout-card__doctitle">{{ activeItem.doc_title }}</div>
              <div class="popout-card__meta-row">
                <span v-if="activeItem.source">{{ activeItem.source }}</span>
                <span v-if="activeItem.date"> · {{ activeItem.date }}</span>
                <span class="popout-card__chunkid">{{ activeItem.chunk_id }}</span>
              </div>
              <a
                v-if="activeItem.url"
                :href="activeItem.url"
                target="_blank"
                rel="noopener noreferrer"
                class="popout-card__link"
              >&nearr; 查看原文</a>
            </div>
          </article>
        </div>
      </Transition>
    </Teleport>
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

const activeItem = ref<ReferenceItem | null>(null)

function open(item: ReferenceItem) {
  activeItem.value = item
}

function close() {
  activeItem.value = null
}

function renderMarkdown(text: string): string {
  return marked.parse(text, { breaks: true, async: false }) as string
}
</script>

<style scoped>
/* ===== Card List ===== */
.reference-list {
  display: grid;
  gap: 12px;
}

.reference-card {
  display: flex;
  gap: 10px;
  padding: 14px;
  border: 1px solid var(--graphite);
  border-radius: 6px;
  transition: border-color 0.15s, background 0.15s, transform 0.15s;
  cursor: pointer;
}

.reference-card:hover {
  border-color: rgba(193, 41, 46, 0.4);
  background: rgba(193, 41, 46, 0.02);
  transform: translateX(2px);
}

.reference-card:active {
  transform: scale(0.99);
}

.reference-card__bar {
  width: 3px;
  border-radius: 2px;
  background: var(--graphite);
  flex-shrink: 0;
  align-self: stretch;
  transition: background 0.2s;
}

.reference-card:hover .reference-card__bar {
  background: rgba(193, 41, 46, 0.3);
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

.reference-card__doctitle {
  font-size: 0.78rem;
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.reference-card__excerpt {
  font-size: 0.85rem;
  line-height: 1.7;
  color: var(--ink);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.reference-card__source-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(26, 26, 46, 0.05);
  font-size: 0.72rem;
  color: var(--muted);
  justify-self: start;
}

/* ===== Pop-out Overlay ===== */
.popout-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  background: rgba(26, 26, 46, 0.35);
  backdrop-filter: blur(4px);
}

/* ===== Pop-out Card ===== */
.popout-card {
  position: relative;
  width: 100%;
  max-width: 620px;
  max-height: 80vh;
  overflow-y: auto;
  padding: 28px 32px;
  background: var(--paper);
  border: 1px solid var(--graphite);
  border-radius: 10px;
  box-shadow:
    0 4px 24px rgba(26, 26, 46, 0.1),
    0 1px 4px rgba(26, 26, 46, 0.05);
  display: grid;
  gap: 20px;
}

.popout-card__close {
  position: absolute;
  top: 12px; right: 16px;
  width: 28px; height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  color: var(--muted);
  transition: all 0.15s;
}
.popout-card__close:hover {
  background: var(--cinnabar-dim);
  color: var(--cinnabar);
}

.popout-card__meta {
  display: flex;
  gap: 10px;
  align-items: center;
}

/* ===== Markdown Content ===== */
.popout-card__content {
  font-size: 0.92rem;
  line-height: 1.85;
  color: var(--ink);
}

.popout-card__content :deep(p) { margin: 0 0 0.8em; }
.popout-card__content :deep(p:last-child) { margin-bottom: 0; }
.popout-card__content :deep(strong) { font-weight: 600; }
.popout-card__content :deep(em) { font-style: italic; }

.popout-card__content :deep(h1),
.popout-card__content :deep(h2),
.popout-card__content :deep(h3),
.popout-card__content :deep(h4) {
  font-family: var(--font-display);
  margin: 1.2em 0 0.5em;
  line-height: 1.4;
}
.popout-card__content :deep(h2) { font-size: 1.1rem; }
.popout-card__content :deep(h3) { font-size: 1rem; }

.popout-card__content :deep(ul),
.popout-card__content :deep(ol) {
  margin: 0.6em 0;
  padding-left: 1.6em;
  line-height: 1.8;
}
.popout-card__content :deep(li) { margin-bottom: 0.3em; }

.popout-card__content :deep(code) {
  font-family: var(--font-mono);
  font-size: 0.88em;
  background: rgba(26, 26, 46, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
}

.popout-card__content :deep(pre) {
  margin: 1em 0;
  padding: 16px 20px;
  background: rgba(26, 26, 46, 0.04);
  border: 1px solid var(--graphite);
  border-radius: 8px;
  overflow-x: auto;
  font-size: 0.85em;
  line-height: 1.7;
}

.popout-card__content :deep(pre code) {
  background: none;
  padding: 0;
  border-radius: 0;
  font-size: inherit;
}

.popout-card__content :deep(blockquote) {
  margin: 0.8em 0;
  padding: 8px 16px;
  border-left: 3px solid var(--cinnabar);
  background: rgba(193, 41, 46, 0.04);
  border-radius: 0 4px 4px 0;
  color: var(--muted);
}

.popout-card__content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.8em 0;
  font-size: 0.88em;
}
.popout-card__content :deep(th),
.popout-card__content :deep(td) {
  padding: 8px 12px;
  border: 1px solid var(--graphite);
  text-align: left;
}
.popout-card__content :deep(th) {
  background: rgba(26, 26, 46, 0.04);
  font-weight: 600;
}

.popout-card__content :deep(hr) {
  border: none;
  border-top: 1px solid var(--graphite);
  margin: 1em 0;
}

/* ===== Pop-out Footer ===== */
.popout-card__footer {
  padding-top: 16px;
  border-top: 1px solid var(--graphite);
  display: grid;
  gap: 6px;
}

.popout-card__doctitle {
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--ink);
}

.popout-card__meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 0.78rem;
  color: var(--muted);
}

.popout-card__chunkid {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--muted);
}

.popout-card__link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--cinnabar);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.85rem;
}
.popout-card__link:hover {
  text-decoration: underline;
}

/* ===== Transition ===== */
.popout-enter-active {
  transition: opacity 0.2s ease;
}
.popout-enter-active .popout-card {
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.2s ease;
}

.popout-leave-active {
  transition: opacity 0.15s ease;
}
.popout-leave-active .popout-card {
  transition: transform 0.15s ease, opacity 0.15s ease;
}

.popout-enter-from {
  opacity: 0;
}
.popout-enter-from .popout-card {
  transform: scale(0.92) translateY(8px);
  opacity: 0;
}

.popout-leave-to {
  opacity: 0;
}
.popout-leave-to .popout-card {
  transform: scale(0.95) translateY(4px);
  opacity: 0;
}

.empty-state {
  color: var(--muted);
  font-size: 0.85rem;
  line-height: 1.7;
}
</style>
