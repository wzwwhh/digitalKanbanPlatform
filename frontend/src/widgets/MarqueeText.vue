<template>
  <div class="marquee-widget">
    <div class="marquee-track">
      <span class="marquee-text" :style="animStyle">{{ p.props.text || '滚动字幕内容' }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const p = defineProps({
  widget: { type: Object, default: () => ({}) },
  props: { type: Object, default: () => ({}) },
})

const speed = computed(() => p.props.speed || 50)
const duration = computed(() => Math.max(5, 200 / speed.value * 10))

const animStyle = computed(() => ({
  animationDuration: `${duration.value}s`,
}))
</script>

<style scoped>
.marquee-widget {
  width: 100%; height: 100%;
  display: flex; align-items: center;
  background: var(--bg-card);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 0 16px;
  box-sizing: border-box;
  overflow: hidden;
}

.marquee-track {
  width: 100%;
  overflow: hidden;
  white-space: nowrap;
}

.marquee-text {
  display: inline-block;
  padding-left: 100%;
  animation: scroll-left linear infinite;
  font-size: 16px;
  color: var(--accent, #00d4ff);
}

@keyframes scroll-left {
  0% { transform: translateX(0); }
  100% { transform: translateX(-200%); }
}
</style>
