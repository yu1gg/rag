# 学斋 (Xueshe) Frontend Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the RAG workspace from "Marginalia" (cinnabar-red annotation) to "学斋·Xueshe" (indigo-cyan scholarly) aesthetic, add a Landing home page with hero section, and upgrade all micro-interactions with smooth animations.

**Architecture:** Global CSS tokens shift from `--cinnabar #C1292E` to `--indigo #2d5a6e`. New `AppHeader.vue` wraps all routes with glassmorphism top bar. `HomeView.vue` rewritten with dark-gradient hero + feature cards. `WorkspaceView.vue` header replaced by AppHeader, indigo left bars throughout. `ReferenceList.vue` dot/border follow new palette.

**Tech Stack:** Vue 3, CSS custom properties, SVG inline, Google Fonts (Noto Serif SC + Noto Sans SC/Inter)

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/assets/main.css` | **Rewrite tokens + restyle** | Indigo palette, paper texture, glass header, shadows, hover effects |
| `frontend/src/components/AppHeader.vue` | **Create** | Fixed glassmorphism top bar with logo + mode switcher + pipeline SVG |
| `frontend/src/views/HomeView.vue` | **Rewrite** | Hero section + feature cards landing page |
| `frontend/src/views/WorkspaceView.vue` | Modify | Remove old header, integrate AppHeader, indigo accent bars |
| `frontend/src/components/ReferenceList.vue` | Modify | Cinnabar → indigo dot/border |
| `frontend/src/components/PipelineIndicator.vue` | Modify | Color references to use CSS vars (auto-adapts) |
| `frontend/src/App.vue` | Modify | Add AppHeader wrapper, router-view layout |

---

### Task 1: Design Tokens Rewrite

**Files:**
- Modify: `frontend/src/assets/main.css`

Replace the `:root` block and base styles:

```css
/* ===== 学斋 (Xueshe) Design System ===== */

:root {
  /* Palette — 靛青书院风格 */
  --indigo:       #2d5a6e;
  --indigo-light: #4a8fa6;
  --indigo-dark:  #1a3d4d;
  --indigo-dim:   rgba(45, 90, 110, 0.08);
  --indigo-glow:  rgba(45, 90, 110, 0.12);

  --paper:        #f8f5ef;
  --card:         #fffdf8;
  --ink:          #1a1a2e;
  --ink-secondary:#4a4a5a;
  --ink-muted:    #8a8a96;
  --border:       #e0d8c8;
  --border-light: #ebe4d6;

  /* Shadows — 暖墨色 */
  --shadow-xs:  0 1px 2px rgba(26,26,46,0.03);
  --shadow-sm:  0 2px 6px rgba(26,26,46,0.05);
  --shadow-md:  0 4px 14px rgba(26,26,46,0.06);
  --shadow-lg:  0 8px 28px rgba(26,26,46,0.08);
  --shadow-glow:0 0 30px rgba(45,90,110,0.10);

  /* Spacing */
  --space-xs:0.25rem; --space-sm:0.5rem; --space-md:1rem;
  --space-lg:1.5rem; --space-xl:2rem; --space-2xl:3rem;

  /* Radius */
  --radius-sm:4px; --radius-md:6px; --radius-lg:10px; --radius-xl:14px; --radius-full:9999px;

  /* Easing */
  --ease-out:  cubic-bezier(0.16, 1, 0.3, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --duration-fast: 0.15s;
  --duration-normal: 0.25s;
  --duration-slow: 0.4s;

  /* Typography — keep existing */
  --font-display: "Noto Serif SC", "Source Han Serif SC", Georgia, serif;
  --font-body:    "Inter", "Noto Sans SC", system-ui, -apple-system, sans-serif;
  --font-mono:    "JetBrains Mono", "Fira Code", Consolas, monospace;

  /* Legacy aliases for old classes that reference cinnabar */
  --cinnabar:     #2d5a6e;
  --cinnabar-dim: rgba(45, 90, 110, 0.08);
  --graphite:     #e0d8c8;
  --highlighter:  rgba(45, 90, 110, 0.06);
  --muted:        #8a8a96;
}
```

Keep the rest of main.css body/base styles, but update:

- Body background: `background: var(--paper);` with paper texture SVG (keep)
- Chat bubble assistance: `border-left: 3px solid var(--indigo)` (was cinnabar)
- Primary button: `background: var(--indigo)` (was cinnabar)
- Mode switcher active: `background: var(--indigo)` 
- Hover/focus states: replace all `--cinnabar` references with `--indigo`
- System status dot: keep green `#16a34a`

- [ ] **Step 1: Replace the `:root` block** with the new tokens above
- [ ] **Step 2: Global search-replace `var(--cinnabar)` → `var(--indigo)`** across entire file
- [ ] **Step 3: Search-replace `var(--cinnabar-dim)` → `var(--indigo-dim)`** 
- [ ] **Step 4: Verify build** — `cd frontend && npm run build 2>&1 | grep "✓ built"`
- [ ] **Step 5: Commit** — `git add frontend/src/assets/main.css && git commit -m "design: xueshe indigo palette, replace cinnabar tokens"`

---

### Task 2: AppHeader Component

**Files:**
- Create: `frontend/src/components/AppHeader.vue`
- Modify: `frontend/src/assets/main.css` (header styles)
- Modify: `frontend/src/App.vue` (wrap with header)

Create `AppHeader.vue`:

```vue
<template>
  <header class="app-header" :class="{ 'app-header--scrolled': scrolled }">
    <div class="app-header__inner">
      <RouterLink to="/" class="app-header__brand">
        <span class="app-header__logo">学斋</span>
        <span class="app-header__tagline">RAG 知识工作台</span>
      </RouterLink>

      <div class="app-header__center">
        <PipelineIndicator :stage="pipelineStage" :active="pipelineActive" />
      </div>

      <nav class="app-header__nav">
        <RouterLink to="/" class="app-header__link" active-class="app-header__link--active">首页</RouterLink>
        <RouterLink to="/qa" class="app-header__link" active-class="app-header__link--active">问答</RouterLink>
        <RouterLink to="/summary" class="app-header__link" active-class="app-header__link--active">摘要</RouterLink>
        <a class="app-header__link" :href="docsUrl" target="_blank" rel="noopener">API</a>
      </nav>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import PipelineIndicator from './PipelineIndicator.vue'

const route = useRoute()
const scrolled = ref(false)
const pipelineStage = computed(() => 0)
const pipelineActive = ref(false)

const docsUrl = computed(() => {
  const base = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8050/api/v1'
  return base.replace(/\/api\/v1\/?$/, '/docs')
})

function onScroll() { scrolled.value = window.scrollY > 20 }
onMounted(() => window.addEventListener('scroll', onScroll))
onUnmounted(() => window.removeEventListener('scroll', onScroll))
</script>

<style scoped>
.app-header {
  position: fixed; top: 0; left: 0; right: 0;
  height: 52px; z-index: 1000;
  background: rgba(248,245,239,0.78);
  backdrop-filter: blur(16px) saturate(160%);
  border-bottom: 1px solid transparent;
  transition: background var(--duration-normal), border-color var(--duration-normal);
}
.app-header--scrolled {
  background: rgba(248,245,239,0.94);
  border-color: var(--border);
}
.app-header__inner {
  max-width: 1540px; margin: 0 auto;
  height: 100%;
  display: flex; align-items: center;
  padding: 0 var(--space-xl); gap: var(--space-xl);
}
.app-header__brand {
  display: flex; align-items: baseline; gap: 8px;
}
.app-header__logo {
  font-family: var(--font-display); font-size: 1.25rem; font-weight: 700;
  color: var(--indigo);
}
.app-header__tagline {
  font-size: 0.75rem; color: var(--ink-muted);
}
.app-header__center { flex: 1; display: flex; justify-content: center; }
.app-header__nav { display: flex; gap: 4px; }
.app-header__link {
  padding: 6px 14px; border-radius: var(--radius-md);
  font-size: 0.85rem; color: var(--ink-secondary);
  transition: color var(--duration-fast), background var(--duration-fast);
}
.app-header__link:hover { color: var(--ink); background: var(--indigo-dim); }
.app-header__link--active { color: var(--indigo); font-weight: 500; }
</style>
```

Update `App.vue`:
```vue
<template>
  <AppHeader />
  <router-view />
</template>
```

Add header CSS to main.css:
```css
.app-header-spacer { height: 52px; }
```

Add spacer to workspace-shell for header offset:
```css
.workspace-shell { padding-top: 52px; height: 100vh; }
```

- [ ] **Step 1: Create AppHeader.vue** and add to `main.css`
- [ ] **Step 2: Update App.vue** to include AppHeader  
- [ ] **Step 3: Update workspace-shell** with padding-top offset
- [ ] **Step 4: Verify build**
- [ ] **Step 5: Commit** — `git add frontend/src/components/AppHeader.vue frontend/src/App.vue frontend/src/assets/main.css && git commit -m "design: add glassmorphism AppHeader with indigo logo"`

---

### Task 3: Landing Home Page

**Files:**
- Modify: `frontend/src/views/HomeView.vue`
- Modify: `frontend/src/assets/main.css` (home styles)

Replace HomeView.vue with a hero-based landing page:

```vue
<template>
  <div class="landing">
    <section class="hero">
      <div class="hero__bg">
        <div class="hero__orb hero__orb--1"></div>
        <div class="hero__orb hero__orb--2"></div>
        <div class="hero__orb hero__orb--3"></div>
      </div>
      <div class="hero__content">
        <h1 class="hero__title">
          <span class="hero__char" v-for="(c, i) in '学斋·知识工作台'" :key="i" :style="{ animationDelay: `${i * 0.08}s` }">{{ c }}</span>
        </h1>
        <p class="hero__subtitle">基于 RAG 的智能问答与文本摘要系统</p>
        <div class="hero__actions">
          <RouterLink to="/qa" class="hero__btn hero__btn--primary">开始问答</RouterLink>
          <RouterLink to="/summary" class="hero__btn hero__btn--secondary">文档摘要</RouterLink>
        </div>
      </div>
      <div class="hero__scroll" aria-hidden="true">
        <span></span>
      </div>
    </section>

    <section class="features">
      <div class="features__header">
        <h2 class="features__title">两大核心能力</h2>
        <p class="features__sub">检索增强生成，让 AI 回答有据可依</p>
      </div>
      <div class="features__grid">
        <RouterLink to="/qa" class="feature-card feature-card--qa">
          <div class="feature-card__icon">🔍</div>
          <h3>智能问答</h3>
          <p>基于本地知识索引和外部大模型，输入问题获取带来源标注的答案。支持向量检索和关键词检索两种模式。</p>
          <span class="feature-card__link">进入问答 →</span>
        </RouterLink>
        <RouterLink to="/summary" class="feature-card feature-card--summary">
          <div class="feature-card__icon">📝</div>
          <h3>文本摘要</h3>
          <p>上传或粘贴长文本，自动生成结构化摘要。核心主题、关键要点、详细摘要一目了然。</p>
          <span class="feature-card__link">进入摘要 →</span>
        </RouterLink>
      </div>
    </section>

    <footer class="landing-footer">
      <span>学斋 · Xueshe RAG Workbench</span>
      <a :href="docsUrl" target="_blank" rel="noopener">API 文档</a>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, computed } from 'vue-router'

const docsUrl = computed(() => {
  const base = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8050/api/v1'
  return base.replace(/\/api\/v1\/?$/, '/docs')
})
</script>
```

Add home styles to main.css:
```css
/* ===== Landing Home ===== */
.landing { overflow-x: hidden; }

/* Hero */
.hero {
  position: relative; display: grid; place-items: center;
  min-height: calc(100vh - 52px); padding: var(--space-4xl) var(--space-xl);
  background: linear-gradient(135deg, #1a1a2e 0%, #2a2a40 30%, #2d5a6e 70%, #3a7d5c 100%);
  overflow: hidden;
}
.hero__bg { position: absolute; inset: 0; }
.hero__orb {
  position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.15;
}
.hero__orb--1 { width: 400px; height: 400px; background: var(--indigo); top: -100px; left: 10%; animation: float-orb 8s ease-in-out infinite; }
.hero__orb--2 { width: 300px; height: 300px; background: #3a7d5c; bottom: -50px; right: 15%; animation: float-orb 10s ease-in-out 1s infinite; }
.hero__orb--3 { width: 250px; height: 250px; background: var(--indigo-light); top: 40%; right: 30%; animation: float-orb 12s ease-in-out 2s infinite; }
@keyframes float-orb { 0%, 100% { transform: translate(0, 0); } 50% { transform: translate(30px, -30px); } }

.hero__content { position: relative; z-index: 1; text-align: center; max-width: 680px; }
.hero__title { font-family: var(--font-display); font-size: clamp(2rem, 5vw, 3rem); font-weight: 700; color: #fff; margin-bottom: var(--space-md); }
.hero__char { display: inline-block; opacity: 0; animation: char-in var(--duration-slow) var(--ease-out) forwards; }
@keyframes char-in { to { opacity: 1; } }

.hero__subtitle { font-size: 1.1rem; color: rgba(255,255,255,0.7); margin-bottom: var(--space-2xl); }
.hero__actions { display: flex; gap: var(--space-md); justify-content: center; flex-wrap: wrap; }
.hero__btn { padding: 12px 32px; border-radius: var(--radius-lg); font-weight: 600; font-size: 0.95rem; transition: all var(--duration-fast); }
.hero__btn--primary { background: #fff; color: var(--indigo); }
.hero__btn--primary:hover { background: rgba(255,255,255,0.9); transform: translateY(-1px); }
.hero__btn--secondary { background: rgba(255,255,255,0.1); color: #fff; border: 1px solid rgba(255,255,255,0.2); }
.hero__btn--secondary:hover { background: rgba(255,255,255,0.18); }

.hero__scroll { position: absolute; bottom: 32px; left: 50%; transform: translateX(-50%); }
.hero__scroll span { display: block; width: 24px; height: 40px; border: 2px solid rgba(255,255,255,0.3); border-radius: 12px; position: relative; }
.hero__scroll span::after { content: ''; position: absolute; top: 6px; left: 50%; transform: translateX(-50%); width: 4px; height: 8px; border-radius: 2px; background: rgba(255,255,255,0.5); animation: scroll-bounce 2s infinite; }
@keyframes scroll-bounce { 0%, 100% { top: 6px; opacity: 1; } 50% { top: 18px; opacity: 0.3; } }

/* Features */
.features { padding: var(--space-4xl) var(--space-xl); max-width: 960px; margin: 0 auto; }
.features__header { text-align: center; margin-bottom: var(--space-2xl); }
.features__title { font-family: var(--font-display); font-size: 1.75rem; color: var(--ink); margin-bottom: var(--space-sm); }
.features__sub { color: var(--ink-muted); }
.features__grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-xl); }

.feature-card {
  display: grid; gap: var(--space-md); padding: 32px;
  border: 1px solid var(--border); border-radius: var(--radius-xl);
  background: var(--card); transition: all var(--duration-normal) var(--ease-out);
}
.feature-card:hover { border-color: var(--indigo); transform: translateY(-3px); box-shadow: var(--shadow-glow); }
.feature-card__icon { font-size: 2rem; }
.feature-card h3 { font-family: var(--font-display); font-size: 1.15rem; margin: 0; }
.feature-card p { font-size: 0.9rem; color: var(--ink-secondary); line-height: 1.7; margin: 0; }
.feature-card__link { font-size: 0.85rem; color: var(--indigo); font-weight: 500; }

.landing-footer { text-align: center; padding: var(--space-2xl); border-top: 1px solid var(--border-light); }
.landing-footer span { color: var(--ink-muted); font-size: 0.82rem; }
.landing-footer a { color: var(--indigo); font-size: 0.82rem; margin-left: var(--space-lg); }
```

- [ ] **Step 1: Replace HomeView.vue** with hero landing
- [ ] **Step 2: Add landing CSS** to main.css
- [ ] **Step 3: Verify build**
- [ ] **Step 4: Commit** — `git add frontend/src/views/HomeView.vue frontend/src/assets/main.css && git commit -m "design: hero landing page with feature cards"`

---

### Task 4: WorkspaceView UI Upgrade

**Files:**
- Modify: `frontend/src/views/WorkspaceView.vue`

1. **Remove old header block** (the `<header class="workspace-header">` and contents)
2. **Change sidebar active bar** color — already uses CSS vars, auto-adapted
3. **Change send button** — already uses `--primary-button` → auto-adapted
4. **Message assistant bubble left bar** — auto-adapted via CSS
5. **Keep mode-switcher and retrieval-switcher** inside the composer

- [ ] **Step 1: Read current header, remove it** (replaced by AppHeader)
- [ ] **Step 2: Add `docsUrl` computed if not present** for API link
- [ ] **Step 3: Verify build**
- [ ] **Step 4: Commit** — `git add frontend/src/views/WorkspaceView.vue && git commit -m "design: remove workspace header, use global AppHeader"`

---

### Task 5: ReferenceList Indigo Makeover

**Files:**
- Modify: `frontend/src/components/ReferenceList.vue`

Replace all cinnabar with indigo:

1. `.reference-card__bar`: `background: var(--indigo)` (pop-out expanded)
2. `.reference-card:hover`: `border-color: var(--indigo-dim)`
3. `.popout-card__close:hover`: `background: var(--indigo-dim); color: var(--indigo)`

- [ ] **Step 1: Replace cinnabar → indigo in scoped styles**
- [ ] **Step 2: Verify build**
- [ ] **Step 3: Commit** — `git add frontend/src/components/ReferenceList.vue && git commit -m "design: reference card indigo accent"`

---

### Task 6: Final Verification

- [ ] **Step 1: Run all tests** — `python -m pytest backend/tests/ -q` (expect ~29 passed)
- [ ] **Step 2: Frontend tests** — `cd frontend && npx vitest run` (expect 5 passed)
- [ ] **Step 3: Build** — `cd frontend && npm run build` (expect ✓ built)
- [ ] **Step 4: Final commit and push**
