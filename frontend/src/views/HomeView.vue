<template>
  <section class="page-card">
    <p class="section-tag">Overview</p>
    <h2>Ver 2.0 已进入前端主交互阶段</h2>
    <p>
      当前前端已经接入主要交互入口，后端主接口为
      <code>/api/v1/health</code>、<code>/api/v1/rag/qa</code>、
      <code>/api/v1/rag/summary</code>。
    </p>
    <div class="info-grid">
      <article>
        <h3>当前阶段</h3>
        <p>首页与两种工具页已经可直接操作，后端 <code>/docs</code> 只保留给接口调试和联调用途。</p>
      </article>
      <article>
        <h3>使用建议</h3>
        <p>日常人工使用请优先走前端页面；需要核对请求参数或调试后端包络时，再打开 <code>/docs</code>。</p>
      </article>
    </div>
  </section>
</template>
