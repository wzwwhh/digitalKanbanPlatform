<template>
  <div class="chart-widget">
    <div class="chart-title">{{ p.props.title || '散点图' }}</div>
    <v-chart class="chart" :option="chartOption" autoresize />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { ScatterChart as EScatterChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'

use([CanvasRenderer, EScatterChart, GridComponent, TooltipComponent])

const p = defineProps({
  widget: { type: Object, default: () => ({}) },
  props: { type: Object, default: () => ({}) },
})

const chartOption = computed(() => {
  const data = p.props.data?.length
    ? p.props.data
    : Array.from({ length: 30 }, () => [
        Math.round(Math.random() * 100),
        Math.round(Math.random() * 100),
      ])

  return {
    tooltip: { trigger: 'item' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'value',
      name: p.props.xName || '',
      splitLine: { lineStyle: { color: '#2a3560' } },
      axisLine: { lineStyle: { color: '#4a5578' } },
    },
    yAxis: {
      type: 'value',
      name: p.props.yName || '',
      splitLine: { lineStyle: { color: '#2a3560' } },
      axisLine: { lineStyle: { color: '#4a5578' } },
    },
    series: [{
      type: 'scatter',
      data,
      symbolSize: 10,
      itemStyle: {
        color: 'rgba(0,212,255,0.7)',
        borderColor: '#00d4ff',
        borderWidth: 1,
      },
      emphasis: {
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,212,255,0.5)' },
      },
    }],
    backgroundColor: 'transparent',
  }
})
</script>

<style scoped>
.chart-widget {
  width: 100%; height: 100%;
  display: flex; flex-direction: column;
  background: var(--bg-card);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  box-sizing: border-box;
  padding: 12px;
}

.chart-title {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.chart {
  width: 100%;
  flex: 1;
  min-height: 0;
}
</style>
