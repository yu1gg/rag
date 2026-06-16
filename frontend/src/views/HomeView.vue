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
          <span class="hero__char" v-for="(c, i) in '知源 · 知识工作台'" :key="i" :style="{ animationDelay: `${i * 0.08}s` }">{{ c }}</span>
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
          <div class="feature-card__icon">&#x1F50D;</div>
          <h3>智能问答</h3>
          <p>基于本地知识索引和外部大模型，输入问题获取带来源标注的答案。支持向量检索和关键词检索两种模式。</p>
          <span class="feature-card__link">进入问答 &rarr;</span>
        </RouterLink>
        <RouterLink to="/summary" class="feature-card feature-card--summary">
          <div class="feature-card__icon">&#x1F4DD;</div>
          <h3>文本摘要</h3>
          <p>上传或粘贴长文本，自动生成结构化摘要。核心主题、关键要点、详细摘要一目了然。</p>
          <span class="feature-card__link">进入摘要 &rarr;</span>
        </RouterLink>
      </div>
    </section>

    <footer class="landing-footer">
      <span>知源 &middot; ZhiYuan RAG Workbench</span>
      <a :href="docsUrl" target="_blank" rel="noopener">API 文档</a>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

const docsUrl = computed(() => {
  const base = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8050/api/v1'
  return base.replace(/\/api\/v1\/?$/, '/docs')
})
</script>
