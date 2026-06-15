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
