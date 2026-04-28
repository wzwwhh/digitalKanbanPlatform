<template>
  <div class="chart-widget">
    <div class="chart-title">{{ p.props.title || '雷达图' }}</div>
    <v-chart class="chart" :option="chartOption" autoresize />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { RadarChart as ERadarChart } from 'echarts/charts'
import { TooltipComponent } from 'echarts/components'

use([CanvasRenderer, ERadarChart, TooltipComponent])

const p = defineProps({
  widget: { type: Object, default: () => ({}) },
  props: { type: Object, default: () => ({}) },
})

const chartOption = computed(() => {
  const indicators = p.props.indicators?.length
    ? p.props.indicators
    : [
        { name: '销售', max: 100 },
        { name: '管理', max: 100 },
        { name: '技术', max: 100 },
        { name: '客服', max: 100 },
        { name: '研发', max: 100 },
      ]

  const values = p.props.values?.length
    ? p.props.values
    : [72, 68, 85, 56, 90]

  return {
    tooltip: {},
    radar: {
      indicator: indicators,
      shape: 'circle',
      splitNumber: 4,
      axisName: { color: '#8892b0', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(0,212,255,0.1)' } },
      splitArea: { areaStyle: { color: ['rgba(0,212,255,0.02)', 'rgba(0,212,255,0.05)'] } },
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.15)' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: values,
        areaStyle: { color: 'rgba(0,212,255,0.15)' },
        lineStyle: { color: '#00d4ff', width: 2 },
        itemStyle: { color: '#00d4ff' },
      }],
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
