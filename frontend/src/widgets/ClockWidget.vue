<template>
  <div class="clock-widget">
    <div class="clock-time">{{ timeText }}</div>
    <div v-if="p.props.showDate !== false" class="clock-date">{{ dateText }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const p = defineProps({
  widget: { type: Object, default: () => ({}) },
  props: { type: Object, default: () => ({}) },
})

const timeText = ref('')
const dateText = ref('')
let timer = null

function updateTime() {
  const now = new Date()
  const is24h = p.props.format !== '12h'
  timeText.value = now.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: !is24h,
  })
  dateText.value = now.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    weekday: 'short',
  })
}

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.clock-widget {
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

.clock-time {
  font-size: 28px;
  font-weight: 700;
  color: var(--accent);
  font-variant-numeric: tabular-nums;
  letter-spacing: 1px;
}

.clock-date {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
