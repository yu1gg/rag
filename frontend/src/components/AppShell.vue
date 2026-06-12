<template>
  <div class="app-shell">
    <header class="app-header">
      <div>
        <p class="eyebrow">project_X</p>
        <h1>Ver 2.0 前端交互入口</h1>
      </div>
      <nav class="app-nav">
        <RouterLink to="/">首页</RouterLink>
        <RouterLink to="/qa">问答</RouterLink>
        <RouterLink to="/summary">摘要</RouterLink>
        <RouterLink to="/search">检索</RouterLink>
      </nav>
    </header>

    <main class="app-main">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>
