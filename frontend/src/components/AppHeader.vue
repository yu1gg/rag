<template>
  <header class="app-header" :class="{ 'app-header--scrolled': scrolled }">
    <div class="app-header__inner">
      <RouterLink to="/" class="app-header__brand">
        <span class="app-header__logo">知源</span>
        <span class="app-header__tagline">RAG 知识工作台</span>
      </RouterLink>

      <nav class="app-header__nav">
        <RouterLink to="/" class="app-header__link" exact-active-class="app-header__link--active">首页</RouterLink>
        <RouterLink to="/qa" class="app-header__link" active-class="app-header__link--active">问答</RouterLink>
        <RouterLink to="/summary" class="app-header__link" active-class="app-header__link--active">摘要</RouterLink>
        <a class="app-header__link" :href="docsUrl" target="_blank" rel="noopener">API</a>
      </nav>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RouterLink } from 'vue-router'

const scrolled = ref(false)

const docsUrl = computed(() => {
  const base = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8050/api/v1'
  return base.replace(/\/api\/v1\/?$/, '/docs')
})

function onScroll() { scrolled.value = window.scrollY > 20 }
onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', onScroll))
</script>

<style scoped>
.app-header {
  position: fixed; top: 0; left: 0; right: 0;
  height: 52px; z-index: 1000;
  background: rgba(248,245,239,0.78);
  backdrop-filter: blur(16px) saturate(160%);
  -webkit-backdrop-filter: blur(16px) saturate(160%);
  border-bottom: 1px solid transparent;
  transition: background 0.25s, border-color 0.25s, box-shadow 0.25s;
}
.app-header--scrolled {
  background: rgba(248,245,239,0.94);
  border-color: var(--border);
  box-shadow: var(--shadow-sm);
}
.app-header__inner {
  max-width: 1540px; margin: 0 auto;
  height: 100%;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 var(--space-xl);
}
.app-header__brand {
  display: flex; align-items: baseline; gap: 8px; flex-shrink: 0;
  text-decoration: none;
}
.app-header__logo {
  font-family: var(--font-display); font-size: 1.25rem; font-weight: 700;
  color: var(--indigo);
}
.app-header__tagline {
  font-size: 0.75rem; color: var(--ink-muted);
}
.app-header__nav { display: flex; gap: 2px; }
.app-header__link {
  padding: 6px 14px; border-radius: var(--radius-md);
  font-size: 0.85rem; color: var(--ink-secondary); text-decoration: none;
  transition: color 0.15s, background 0.15s;
}
.app-header__link:hover { color: var(--ink); background: var(--indigo-dim); }
.app-header__link--active { color: var(--indigo); font-weight: 500; background: var(--indigo-dim); }
</style>
