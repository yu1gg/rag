# Marginalia Frontend Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the RAG chat workspace from a generic frosted-glass AI-template into a distinctive "Marginalia" scholar annotation design with a pipeline visualization SVG.

**Architecture:** Complete CSS rewrite with new design tokens (ivory paper, ink blue, cinnabar red), serif headings, collapsible sidebar, marginalia-style reference panel with red dot markers, and a new `PipelineIndicator.vue` SVG component. `AppShell.vue` is removed since `WorkspaceView.vue` is self-contained.

**Tech Stack:** Vue 3, CSS custom properties, SVG inline, Google Fonts (Noto Serif SC, Inter)

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `frontend/index.html` | Modify | Add Google Fonts preconnect + link |
| `frontend/src/assets/main.css` | **Rewrite** | Complete design system from scratch |
| `frontend/src/components/PipelineIndicator.vue` | Create | SVG pipeline visualization |
| `frontend/src/views/WorkspaceView.vue` | Modify | Header, sidebar, chat, panel, composer restructure |
| `frontend/src/components/ReferenceList.vue` | Modify | Marginalia-style reference cards |
| `frontend/src/components/AppShell.vue` | Delete | No longer needed |
| `frontend/src/views/HomeView.vue` | Modify | Match new design language |
| `frontend/src/router/index.ts` | Modify | Remove AppShell if used, ensure standalone routes |
| `frontend/src/main.ts` | Modify | Remove AppShell if imported |

---

### Task 1: Design Tokens Foundation

**Files:**
- Modify: `frontend/index.html`
- Rewrite: `frontend/src/assets/main.css`

- [ ] **Step 1: Add Google Fonts to `index.html`**

In `<head>`, before `<title>`:
```html
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Noto+Serif+SC:wght@500;700&display=swap" rel="stylesheet" />
```

- [ ] **Step 2: Rewrite `main.css` — Design Tokens + Reset**

Replace entire file content:

```css
/* ===== Marginalia Design System ===== */

:root {
  /* Palette */
  --paper:        #FBF9F3;
  --ink:          #1A1A2E;
  --cinnabar:     #C1292E;
  --cinnabar-dim: #F5E1E1;
  --graphite:     #E5E0D8;
  --highlighter:  #FEF3C7;
  --muted:        rgba(26, 26, 46, 0.62);

  /* Typography */
  --font-display: "Noto Serif SC", "Source Han Serif SC", Georgia, serif;
  --font-body:    "Inter", "Noto Sans SC", system-ui, -apple-system, sans-serif;
  --font-mono:    "JetBrains Mono", "Fira Code", Consolas, monospace;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; }

body {
  font-family: var(--font-body);
  color: var(--ink);
  background: var(--paper);
  /* Subtle paper texture via CSS noise */
  background-image:
    url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}

h1, h2, h3, h4 { font-family: var(--font-display); font-weight: 500; line-height: 1.3; }
h1 { font-size: 1.75rem; letter-spacing: -0.01em; }
h2 { font-size: 1.25rem; }
h3 { font-size: 1rem; }

code, pre, .mono { font-family: var(--font-mono); font-size: 0.85em; }

a { color: inherit; text-decoration: none; }
button { font-family: inherit; cursor: pointer; border: none; background: none; }
input, textarea { font-family: inherit; }

#app { min-height: 100vh; }
```

- [ ] **Step 3: Add workspace shell layout**

Append to `main.css`:

```css
/* ===== Workspace Shell ===== */
.workspace-shell {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr) 320px;
  gap: 0;
  min-height: 100vh;
  max-width: 1540px;
  margin: 0 auto;
}

.workspace-sidebar {
  padding: 24px 20px;
  border-right: 1px solid var(--graphite);
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 16px;
  overflow-y: auto;
}

.workspace-main {
  display: grid;
  grid-template-rows: auto 1fr auto;
  min-height: 100vh;
  padding: 24px 32px;
  gap: 20px;
}

.workspace-info {
  padding: 24px 20px;
  border-left: 1px solid var(--graphite);
  overflow-y: auto;
}
```

- [ ] **Step 4: Verify build**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

- [ ] **Step 5: Commit**

```bash
git add frontend/index.html frontend/src/assets/main.css
git commit -m "design: marginalia design tokens, fonts, and layout foundation"
```

---

### Task 2: Header Redesign + Pipeline SVG Component

**Files:**
- Create: `frontend/src/components/PipelineIndicator.vue`
- Modify: `frontend/src/views/WorkspaceView.vue` (header section)
- Modify: `frontend/src/assets/main.css` (header styles)

- [ ] **Step 1: Create `PipelineIndicator.vue`**

```vue
<template>
  <svg
    class="pipeline-indicator"
    :class="{ 'pipeline-indicator--active': active }"
    viewBox="0 0 220 32"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <!-- Stage 1: 检索 -->
    <circle cx="12" cy="16" r="5" :fill="stage >= 1 ? 'var(--ink)' : 'var(--graphite)'" />
    <text x="22" y="20" font-size="8" :fill="stage >= 1 ? 'var(--ink)' : 'var(--graphite)'" font-family="var(--font-body)">检索</text>

    <!-- Arrow 1 -->
    <line x1="62" y1="16" x2="86" y2="16" :stroke="stage >= 2 ? 'var(--ink)' : 'var(--graphite)'" stroke-width="1" />

    <!-- Stage 2: 重排 -->
    <circle cx="98" cy="16" r="5" :fill="stage >= 2 ? 'var(--ink)' : 'var(--graphite)'" />
    <text x="108" y="20" font-size="8" :fill="stage >= 2 ? 'var(--ink)' : 'var(--graphite)'" font-family="var(--font-body)">重排</text>

    <!-- Arrow 2 -->
    <line x1="148" y1="16" x2="172" y2="16" :stroke="stage >= 3 ? 'var(--ink)' : 'var(--graphite)'" stroke-width="1" />

    <!-- Stage 3: 生成 -->
    <circle cx="184" cy="16" r="5" :fill="stage >= 3 ? 'var(--cinnabar)' : 'var(--graphite)'" />
    <text x="194" y="20" font-size="8" :fill="stage >= 3 ? 'var(--cinnabar)' : 'var(--graphite)'" font-family="var(--font-body)">生成</text>
  </svg>
</template>

<script setup lang="ts">
defineProps<{ stage: number; active: boolean }>()
</script>

<style scoped>
.pipeline-indicator {
  width: 220px;
  height: 32px;
  opacity: 0.5;
  transition: opacity 0.3s;
}
.pipeline-indicator--active {
  opacity: 1;
}
</style>
```

- [ ] **Step 2: Redesign header in `WorkspaceView.vue`**

Replace the header block (lines 50-72):
```html
      <header class="workspace-header">
        <div class="workspace-header__lead">
          <button
            class="ghost-button ghost-button--mobile"
            type="button"
            @click="mobileSessionsOpen = !mobileSessionsOpen"
          >
            {{ mobileSessionsOpen ? '收起会话' : '打开会话' }}
          </button>
          <h1 class="workspace-header__title">project_X</h1>
        </div>

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
```

- [ ] **Step 3: Add `pipelineStage` computed + import to script**

In WorkspaceView.vue script:
```typescript
import PipelineIndicator from '../components/PipelineIndicator.vue'

const pipelineStage = computed(() => {
  if (!activeSession.value?.messages.length) return 0
  const last = activeSession.value.messages[activeSession.value.messages.length - 1]
  if (last.role === 'user' || last.status === 'loading') return 1
  if (last.status === 'success') return 3
  return 0
})
```

- [ ] **Step 4: Add header styles to `main.css`**

```css
/* ===== Header ===== */
.workspace-header {
  display: flex;
  align-items: center;
  gap: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--graphite);
}

.workspace-header__title {
  font-family: var(--font-display);
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--ink);
}

.workspace-header__center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.workspace-header__actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-link {
  font-size: 0.85rem;
  color: var(--muted);
  padding: 4px 10px;
  border-radius: 6px;
  transition: color 0.15s, background 0.15s;
}
.header-link:hover { color: var(--ink); background: var(--highlighter); }

.mode-switcher {
  display: flex;
  gap: 2px;
  background: var(--graphite);
  border-radius: 8px;
  padding: 3px;
}

.mode-switcher__button {
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--muted);
  transition: all 0.15s;
}
.mode-switcher__button--active {
  background: var(--paper);
  color: var(--ink);
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
```

- [ ] **Step 5: Verify build**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/PipelineIndicator.vue frontend/src/views/WorkspaceView.vue frontend/src/assets/main.css
git commit -m "design: new header with pipeline SVG and mode switcher"
```

---

### Task 3: Chat Area — Marginalia Bubbles

**Files:**
- Modify: `frontend/src/assets/main.css`
- Modify: `frontend/src/views/WorkspaceView.vue` (bubble template)

- [ ] **Step 1: Add chat bubble styles to `main.css`**

```css
/* ===== Chat Stage ===== */
.chat-stage {
  overflow-y: auto;
  padding: 8px 0;
}

.message-list {
  display: grid;
  gap: 24px;
}

.welcome-panel {
  display: grid;
  gap: 12px;
  padding: 40px 0;
  text-align: center;
}

.welcome-panel h2 {
  font-family: var(--font-display);
  font-size: 1.5rem;
  color: var(--ink);
}

.welcome-panel p {
  color: var(--muted);
  max-width: 420px;
  margin: 0 auto;
}

.welcome-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 16px;
  max-width: 520px;
  margin-left: auto;
  margin-right: auto;
}

.welcome-grid article {
  padding: 20px;
  border: 1px solid var(--graphite);
  border-radius: 8px;
  text-align: left;
}

.welcome-grid article h3 {
  margin-bottom: 8px;
}

.welcome-grid article p {
  font-size: 0.85rem;
  margin: 0;
}

/* Chat Messages */
.chat-message {
  display: grid;
  gap: 6px;
  padding: 4px 0;
  cursor: pointer;
  transition: background 0.15s;
}

.chat-message:hover {
  background: rgba(193, 41, 46, 0.03);
}

.chat-message--selected {
  background: var(--highlighter);
}

.chat-message__meta {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 0.78rem;
  color: var(--muted);
}

.chat-message--user .chat-message__meta { justify-content: flex-end; }

.chat-message__bubble {
  max-width: min(680px, 100%);
  padding: 16px 20px;
  border-radius: 2px 8px 8px 8px;
  line-height: 1.8;
  font-size: 0.95rem;
  position: relative;
}

.chat-message--user .chat-message__bubble {
  justify-self: end;
  background: var(--highlighter);
  border: 1px solid var(--graphite);
}

.chat-message--assistant .chat-message__bubble {
  justify-self: start;
  background: #FFFFFF;
  border: 1px solid var(--graphite);
  /* Marginalia red line on the left */
  border-left: 3px solid var(--cinnabar);
  padding-left: 24px;
}

.chat-message--assistant.chat-message--loading .chat-message__bubble {
  border-left-color: var(--graphite);
}

.chat-message--error .chat-message__bubble {
  background: var(--cinnabar-dim);
  border-color: var(--cinnabar);
  border-left: 3px solid var(--cinnabar);
}

.chat-message__bubble p {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Loading dots */
.chat-message__loading {
  display: inline-flex;
  gap: 5px;
  margin-top: 8px;
}
.chat-message__loading span {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--graphite);
  animation: blink 1.4s infinite ease-in-out;
}
.chat-message__loading span:nth-child(2) { animation-delay: 0.16s; }
.chat-message__loading span:nth-child(3) { animation-delay: 0.32s; }

@keyframes blink {
  0%, 80%, 100% { opacity: 0.3; }
  40% { opacity: 1; }
}

.mode-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  background: var(--graphite);
  color: var(--muted);
}
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/assets/main.css
git commit -m "design: marginalia chat bubbles with red annotation line"
```

---

### Task 4: Right Panel — Marginalia References

**Files:**
- Modify: `frontend/src/assets/main.css`
- Modify: `frontend/src/views/WorkspaceView.vue` (right panel template)
- Modify: `frontend/src/components/ReferenceList.vue`

- [ ] **Step 1: Rewrite right panel in `WorkspaceView.vue`**

Replace the entire right panel section (from `aside.workspace-info` around line 257 to end of `aside` around line 315):

```html
    <aside class="workspace-info">
      <div class="info-card__header">
        <div>
          <h2>批注来源</h2>
          <p class="info-subtitle">
            {{ selectedDetailMessage ? '点击消息的回看详情' : '最新回答的参考来源' }}
          </p>
        </div>
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

      <!-- System status: compact footer -->
      <div class="system-status">
        <span class="status-dot" :class="{ 'status-dot--ok': healthState.data?.index_ready }"></span>
        <span class="system-status__label">索引就绪</span>
        <span class="status-dot" :class="{ 'status-dot--ok': indexState.data?.index_ready }" style="margin-left: 12px"></span>
        <span class="system-status__label">{{ indexState.data?.vector_count ?? 0 }} 向量</span>
      </div>
    </aside>
```

- [ ] **Step 2: Add right panel styles to `main.css`**

```css
/* ===== Marginalia Panel (Right) ===== */
.info-subtitle {
  font-size: 0.8rem;
  color: var(--muted);
  margin-top: 4px;
}

.detail-block {
  margin-top: 20px;
}

.detail-block__meta {
  display: flex;
  gap: 10px;
  align-items: center;
  font-size: 0.78rem;
  color: var(--muted);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--graphite);
}

.empty-state {
  color: var(--muted);
  font-size: 0.85rem;
  margin-top: 20px;
  line-height: 1.7;
}

.system-status {
  margin-top: auto;
  padding-top: 20px;
  border-top: 1px solid var(--graphite);
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
  color: var(--muted);
}

.system-status__label { margin-right: 4px; }

.status-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--graphite);
  flex-shrink: 0;
}
.status-dot--ok { background: #16a34a; }

.summary-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 8px;
}

.summary-stat {
  padding: 14px;
  border: 1px solid var(--graphite);
  border-radius: 6px;
  text-align: center;
}

.summary-stat__label {
  display: block;
  font-size: 0.75rem;
  color: var(--muted);
  margin-bottom: 4px;
}

.summary-stat strong {
  font-size: 1.15rem;
}
```

- [ ] **Step 3: Update `ReferenceList.vue` for marginalia style**

Replace the template:
```vue
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
```

And add scoped styles:
```vue
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
```

- [ ] **Step 4: Remove old styles from `main.css`**

Remove all old styles for `.reference-list`, `.reference-card`, `.reference-meta`, `.reference-badge`, `.reference-excerpt`, `.info-card`, `.status-panel`, `.status-stack`, `.summary-stats article`, `.detail-note`, `.mode-badge--muted`, and `.workspace-info .empty-state` — these are replaced by the new styles above or moved to component scoped CSS.

- [ ] **Step 5: Add `mode-badge--muted` replacement style to `main.css`**

```css
.mode-badge--muted {
  background: rgba(193, 41, 46, 0.08);
  color: var(--cinnabar);
}
```

- [ ] **Step 6: Verify build**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/assets/main.css frontend/src/views/WorkspaceView.vue frontend/src/components/ReferenceList.vue
git commit -m "design: marginalia right panel with red-dot references"
```

---

### Task 5: Collapsible Sidebar + Composer Restyle

**Files:**
- Modify: `frontend/src/views/WorkspaceView.vue` (sidebar + composer template)
- Modify: `frontend/src/assets/main.css`

- [ ] **Step 1: Add sidebar collapse toggle**

Add `sidebarCollapsed` ref in WorkspaceView script:
```typescript
const sidebarCollapsed = ref(false)
```

Update sidebar template to support collapse:
```html
    <aside
      class="workspace-sidebar"
      :class="{
        'workspace-sidebar--collapsed': sidebarCollapsed,
        'workspace-sidebar--open': mobileSessionsOpen
      }"
    >
      <div class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
        {{ sidebarCollapsed ? '▶' : '◀' }}
      </div>
      <template v-if="!sidebarCollapsed">
        <div class="sidebar-head">
          <div>
            <h2 class="sidebar-head__title">会话</h2>
          </div>
          <button class="sidebar-new-btn" type="button" @click="handleNewSession">
            +
          </button>
        </div>
        <div class="session-list">
          <!-- existing session items, unchanged -->
        </div>
      </template>
    </aside>
```

- [ ] **Step 2: Add sidebar styles**

```css
/* ===== Collapsible Sidebar ===== */
.sidebar-toggle {
  position: absolute;
  top: 16px;
  right: -14px;
  width: 28px; height: 28px;
  border-radius: 50%;
  background: var(--paper);
  border: 1px solid var(--graphite);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.65rem;
  color: var(--muted);
  cursor: pointer;
  z-index: 2;
  transition: color 0.15s;
}
.sidebar-toggle:hover { color: var(--ink); }

.workspace-sidebar {
  position: relative;
  transition: width 0.25s ease;
}
.workspace-sidebar--collapsed { width: 48px; min-width: 48px; padding: 24px 8px; }

.sidebar-head__title {
  font-size: 1rem;
  margin: 0;
}

.sidebar-new-btn {
  width: 28px; height: 28px;
  border-radius: 6px;
  background: var(--graphite);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  font-weight: 500;
  color: var(--muted);
  transition: all 0.15s;
}
.sidebar-new-btn:hover { background: var(--cinnabar); color: white; }

.session-list {
  display: grid;
  gap: 6px;
  margin-top: 8px;
}

.session-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: 12px 14px;
  border-radius: 6px;
  border: 1px solid transparent;
  font-size: 0.85rem;
  transition: all 0.15s;
  position: relative;
  overflow: hidden;
}

.session-item:hover {
  background: var(--highlighter);
  border-color: var(--graphite);
}

.session-item--active {
  background: rgba(193, 41, 46, 0.04);
  border-color: var(--cinnabar);
}

.session-item__body {
  display: grid;
  gap: 4px;
}

.session-item__meta {
  display: flex;
  gap: 8px;
  font-size: 0.72rem;
  color: var(--muted);
}

.session-item__body strong {
  font-weight: 500;
  font-size: 0.88rem;
}

.session-item__body p {
  font-size: 0.78rem;
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-item__delete {
  position: absolute;
  top: 8px; right: 8px;
  width: 20px; height: 20px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  color: var(--muted);
  opacity: 0;
  transition: all 0.15s;
}
.session-item:hover .session-item__delete { opacity: 1; }
.session-item__delete:hover { background: var(--cinnabar-dim); color: var(--cinnabar); }
```

- [ ] **Step 3: Update composer styles**

```css
/* ===== Composer ===== */
.composer {
  padding: 16px 0 0;
  border-top: 1px solid var(--graphite);
}

.retrieval-switcher {
  display: flex;
  gap: 2px;
  margin-bottom: 10px;
  align-items: center;
}

.retrieval-switcher__label {
  font-size: 0.78rem;
  color: var(--muted);
  margin-right: 8px;
}

.retrieval-switcher__button {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 0.8rem;
  color: var(--muted);
  transition: all 0.15s;
}
.retrieval-switcher__button--active {
  background: var(--ink);
  color: white;
}

.composer-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-items: center;
  margin-bottom: 12px;
}

.composer-toolbar__hint {
  font-size: 0.75rem;
  color: var(--muted);
  margin: 0 0 0 auto;
}

.compact-field {
  display: flex;
  align-items: center;
  gap: 8px;
}

.compact-field span {
  font-size: 0.78rem;
  color: var(--muted);
  font-weight: 500;
}

.compact-field input {
  width: 64px;
  padding: 6px 10px;
  border: 1px solid var(--graphite);
  border-radius: 6px;
  font-size: 0.85rem;
  text-align: center;
  background: white;
  transition: border-color 0.15s;
}
.compact-field input:focus {
  outline: none;
  border-color: var(--cinnabar);
}

.composer-box {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
}

.composer-box__input {
  padding: 14px 18px;
  border: 1px solid var(--graphite);
  border-radius: 8px;
  font-size: 0.95rem;
  line-height: 1.7;
  resize: vertical;
  min-height: 100px;
  background: white;
  transition: border-color 0.15s;
}
.composer-box__input:focus {
  outline: none;
  border-color: var(--cinnabar);
}

.composer-box__input:disabled {
  background: var(--graphite);
  opacity: 0.6;
}

.composer-error {
  padding: 10px 14px;
  margin-bottom: 10px;
  background: var(--cinnabar-dim);
  color: var(--cinnabar);
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
}

.composer-footnote {
  font-size: 0.72rem;
  color: var(--muted);
  margin-top: 8px;
}
```

- [ ] **Step 4: Primary button restyle**

```css
/* ===== Buttons ===== */
.primary-button {
  padding: 12px 28px;
  border-radius: 8px;
  background: var(--cinnabar);
  color: white;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.15s;
  align-self: end;
}
.primary-button:hover {
  background: #A0232A;
}
.primary-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ghost-button {
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 0.82rem;
  color: var(--muted);
  transition: all 0.15s;
}
.ghost-button:hover { background: var(--graphite); color: var(--ink); }
```

- [ ] **Step 5: Remove old styles from `main.css`**

Remove all old styles for: `.eyebrow`, `.section-tag`, `.sidebar-head`, `.sidebar-note`, `.workspace-header__lead`, `.workspace-subtitle`, `.workspace-header__actions`, `.header-link`, `.ghost-button`, `.primary-button`, `.ghost-button--mobile`, `.mode-switcher__button`, `.composer-toolbar`, `.compact-field`, `.composer-box`, `.composer-box__input`, `.composer-error`, `.composer-footnote`, `.compact-field span`, `.compact-field input`, `.summary-stats`, `.session-item`, `.session-item__body`, `.session-item__meta`, `.session-item__delete`, `.session-item--active`, `.info-card`, `.info-card__header`, `.status-stack`, `.status-panel`, `.status-panel__head`, `.status-panel__error`, `.status-dot`, `.status-dot--ok`, `.mode-badge`, `.mode-badge--muted`, `.detail-block`, `.detail-block__meta`, `.detail-note`, `.welcome-panel`, `.welcome-grid`, `.welcome-grid article`, `.chat-message__bubble p`, `.chat-message__loading span`, `@keyframes blink`.

- [ ] **Step 6: Remove old export of `mode-switcher__button` styles** — they were in Task 2 header styles already.

- [ ] **Step 7: Verify build**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

- [ ] **Step 8: Commit**

```bash
git add frontend/src/views/WorkspaceView.vue frontend/src/assets/main.css
git commit -m "design: collapsible sidebar and restyled composer"
```

---

### Task 6: Cleanup — Remove AppShell and Old Code

**Files:**
- Delete: `frontend/src/components/AppShell.vue`
- Modify: `frontend/src/views/HomeView.vue`
- Modify: `frontend/src/router/index.ts`
- Read then Modify: `frontend/src/main.ts`

- [ ] **Step 1: Delete AppShell.vue**

```bash
rm frontend/src/components/AppShell.vue
```

- [ ] **Step 2: Update HomeView.vue**

Replace the content of `HomeView.vue` to match the new design language:
```vue
<template>
  <section class="home-page">
    <h1 class="home-title">project_X</h1>
    <p class="home-subtitle">基于 RAG 的智能问答与文本摘要系统</p>
    <div class="home-grid">
      <RouterLink to="/qa" class="home-card">
        <h3>智能问答</h3>
        <p>基于本地知识索引和外部大模型，输入问题获取带来源标注的答案。</p>
      </RouterLink>
      <RouterLink to="/summary" class="home-card">
        <h3>文本摘要</h3>
        <p>对长文本进行摘要压缩，支持超长文本的分段摘要与合并。</p>
      </RouterLink>
    </div>
    <p class="home-footer">API 调试入口：<code>/docs</code></p>
  </section>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>
```

- [ ] **Step 3: Add HomeView styles to `main.css`**

```css
/* ===== Home Page ===== */
.home-page {
  display: grid;
  place-content: center;
  min-height: 100vh;
  text-align: center;
  gap: 20px;
  padding: 40px;
}

.home-title {
  font-family: var(--font-display);
  font-size: 2.5rem;
  font-weight: 700;
}

.home-subtitle {
  font-size: 1rem;
  color: var(--muted);
}

.home-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  max-width: 520px;
  margin: 0 auto;
}

.home-card {
  padding: 28px 24px;
  border: 1px solid var(--graphite);
  border-radius: 8px;
  text-align: left;
  transition: all 0.15s;
}

.home-card:hover {
  border-color: var(--cinnabar);
  background: rgba(193, 41, 46, 0.03);
}

.home-card h3 {
  font-family: var(--font-display);
  font-size: 1.1rem;
  margin-bottom: 8px;
}

.home-card p {
  font-size: 0.85rem;
  color: var(--muted);
  line-height: 1.6;
}

.home-footer {
  font-size: 0.8rem;
  color: var(--muted);
  margin-top: 16px;
}

.home-footer code {
  font-family: var(--font-mono);
  background: var(--graphite);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.85em;
}
```

- [ ] **Step 4: Update router if needed**

Read `frontend/src/router/index.ts`. If it imports AppShell, remove the import. If HomeView uses a layout component, update to use direct component rendering.

- [ ] **Step 5: Update main.ts if needed**

Read `frontend/src/main.ts`. If AppShell is used as a global wrapper component, either remove it or update the import.

- [ ] **Step 6: Verify build**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/AppShell.vue frontend/src/views/HomeView.vue frontend/src/router/index.ts frontend/src/main.ts frontend/src/assets/main.css
git commit -m "design: remove AppShell, restyle HomeView, add home CSS"
```

---

### Task 7: Responsive + Final Polish

**Files:**
- Modify: `frontend/src/assets/main.css`

- [ ] **Step 1: Add responsive breakpoints to `main.css`**

```css
/* ===== Responsive ===== */
@media (max-width: 1180px) {
  .workspace-shell {
    grid-template-columns: 200px minmax(0, 1fr) 280px;
  }
}

@media (max-width: 820px) {
  .workspace-shell {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr auto;
  }

  .workspace-sidebar {
    display: none;
    position: fixed;
    top: 0; left: 0; bottom: 0;
    width: 280px;
    z-index: 100;
    background: var(--paper);
    box-shadow: 2px 0 24px rgba(0,0,0,0.12);
  }

  .workspace-sidebar--open { display: grid; }

  .workspace-info {
    border-left: none;
    border-top: 1px solid var(--graphite);
  }

  .workspace-main {
    padding: 16px;
    min-height: auto;
  }

  .ghost-button--mobile { display: inline-flex; }

  .welcome-grid {
    grid-template-columns: 1fr;
  }

  .home-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .workspace-main { padding: 12px; }

  .chat-message__bubble {
    max-width: 100%;
  }

  .composer-box {
    grid-template-columns: 1fr;
  }

  .pipeline-indicator {
    display: none;
  }
}
```

- [ ] **Step 2: Add reduced motion support**

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

- [ ] **Step 3: Verify build + run tests**

```bash
cd frontend && npm run build 2>&1 | tail -5
cd frontend && npx vitest run 2>&1 | tail -5
```
Expected: Build OK, 5 tests passed

- [ ] **Step 4: Final commit**

```bash
git add frontend/src/assets/main.css
git commit -m "design: responsive breakpoints and reduced motion support"
```

---

### Task 8: Final Verification

- [ ] **Step 1: Run frontend tests**

```bash
cd frontend && npx vitest run 2>&1 | tail -5
```
Expected: 5 passed

- [ ] **Step 2: Build frontend**

```bash
cd frontend && npm run build 2>&1 | tail -5
```
Expected: Build succeeds

- [ ] **Step 3: Verify backend tests still pass**

```bash
python -m pytest backend/tests/ -q
```
Expected: ~29 passed

- [ ] **Step 4: Push**

```bash
git add -A
git commit -m "chore: final verification of Marginalia redesign"
git push
```
