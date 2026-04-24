<template>
  <div class="chart-widget">
    <div class="chart-title">{{ props.title }}</div>
    <v-chart class="chart" :option="chartOption" autoresize />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart as ELineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'

use([CanvasRenderer, ELineChart, GridComponent, TooltipComponent, LegendComponent])

const p = defineProps({
  props: {
    type: Object,
    default: () => ({
      title: '折线图',
      smooth: true,
      area: false,
    })
  }
})

// 示例数据（真实数据通过 dataSource 注入）
const chartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { top: 10, right: 16, bottom: 24, left: 40 },
  xAxis: {
    type: 'category',
    data: ['1月', '2月', '3月', '4月', '5月', '6月'],
    axisLine: { lineStyle: { color: 'var(--text-muted)' } },
    axisLabel: { color: 'var(--text-secondary)' },
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: 'var(--border-color)', type: 'dashed' } },
    axisLabel: { color: 'var(--text-secondary)' },
  },
  series: [{
    type: 'line',
    data: [820, 932, 901, 1234, 1090, 1330],
    smooth: p.props.smooth,
    areaStyle: p.props.area ? { opacity: 0.15 } : undefined,
    lineStyle: { color: 'var(--accent)', width: 2 },
    itemStyle: { color: 'var(--accent)' },
  }]
}))
</script>

<style scoped>
.chart-widget {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  padding: 12px;
  box-sizing: border-box;
}

.chart-title {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.chart {
  flex: 1;
  min-height: 0;
}
</style>
