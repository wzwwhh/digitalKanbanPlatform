<template>
  <div class="progress-widget">
    <div class="progress-title">{{ p.props.title || '进度' }}</div>
    <div class="ring-container">
      <svg viewBox="0 0 120 120" class="ring-svg">
        <!-- 背景环 -->
        <circle cx="60" cy="60" r="50" fill="none"
          stroke="var(--bg-tertiary, #1a2045)" stroke-width="10" />
        <!-- 进度环 -->
        <circle cx="60" cy="60" r="50" fill="none"
          :stroke="ringColor"
          stroke-width="10"
          stroke-linecap="round"
          :stroke-dasharray="circumference"
          :stroke-dashoffset="dashOffset"
          class="ring-progress"
        />
      </svg>
      <div class="ring-value" :style="{ color: ringColor }">{{ displayPercent }}%</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const p = defineProps({
  widget: { type: Object, default: () => ({}) },
  props: { type: Object, default: () => ({}) },
})

const displayPercent = computed(() => {
  const v = Number(p.props.percent) || 0
  return Math.min(100, Math.max(0, v))
})

const circumference = 2 * Math.PI * 50 // ≈ 314.16

const dashOffset = computed(() => {
  return circumference * (1 - displayPercent.value / 100)
})

const ringColor = computed(() => {
  if (p.props.color) return p.props.color
  const pct = displayPercent.value
  if (pct >= 80) return '#00e396'
  if (pct >= 50) return 'var(--accent, #00d4ff)'
  if (pct >= 30) return '#feb019'
  return '#ff4560'
})
</script>

<style scoped>
.progress-widget {
  width: 100%; height: 100%;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  background: var(--bg-card);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 12px;
  box-sizing: border-box;
}

.progress-title {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.ring-container {
  position: relative;
  width: 100px;
  height: 100px;
}

.ring-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-progress {
  transition: stroke-dashoffset 0.6s ease;
}

.ring-value {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 700;
}
</style>
