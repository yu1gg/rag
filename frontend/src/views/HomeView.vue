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
