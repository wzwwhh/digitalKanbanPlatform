<template>
  <div class="echarts-custom-widget">
    <div class="custom-title" v-if="props.title">{{ props.title }}</div>
    <div ref="chartRef" class="custom-chart"></div>
    <div class="no-option" v-if="!props.option">
      粘贴 ECharts option JSON 到属性面板
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, inject } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  title: { type: String, default: '' },
  option: { type: String, default: '' },  // JSON string of ECharts option
})

const themeVars = inject('themeVars', {})
const chartRef = ref(null)
let chart = null

function renderChart() {
  if (!chartRef.value || !props.option) return
  try {
    const option = JSON.parse(props.option)
    if (!chart) {
      chart = echarts.init(chartRef.value)
    }
    // Apply theme-aware defaults
    if (!option.backgroundColor) option.backgroundColor = 'transparent'
    chart.setOption(option, true)
    nextTick(() => chart?.resize())
  } catch (e) {
    console.warn('[EchartsCustom] Invalid option JSON:', e.message)
  }
}

onMounted(() => {
  renderChart()
  window.addEventListener('resize', () => chart?.resize())
})

onUnmounted(() => {
  chart?.dispose()
  chart = null
})

watch(() => props.option, renderChart)
</script>

<style scoped>
.echarts-custom-widget {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card, #161d42);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 12px;
  overflow: hidden;
  padding: 12px;
}

.custom-title {
  font-size: 14px;
  color: var(--text-secondary, #8892b0);
  margin-bottom: 8px;
}

.custom-chart {
  flex: 1;
  min-height: 0;
}

.no-option {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--text-muted, #4a5578);
  font-size: 13px;
}
</style>
