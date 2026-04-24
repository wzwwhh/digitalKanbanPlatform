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
import { BarChart as EBarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'

use([CanvasRenderer, EBarChart, GridComponent, TooltipComponent])

const p = defineProps({
  props: {
    type: Object,
    default: () => ({
      title: '柱状图',
      stack: false,
      horizontal: false,
    })
  }
})

const chartOption = computed(() => {
  const categoryAxis = {
    type: 'category',
    data: ['产品A', '产品B', '产品C', '产品D', '产品E'],
    axisLine: { lineStyle: { color: 'var(--text-muted)' } },
    axisLabel: { color: 'var(--text-secondary)' },
  }
  const valueAxis = {
    type: 'value',
    splitLine: { lineStyle: { color: 'var(--border-color)', type: 'dashed' } },
    axisLabel: { color: 'var(--text-secondary)' },
  }

  return {
    tooltip: { trigger: 'axis' },
    grid: { top: 10, right: 16, bottom: 24, left: 40 },
    xAxis: p.props.horizontal ? valueAxis : categoryAxis,
    yAxis: p.props.horizontal ? categoryAxis : valueAxis,
    series: [{
      type: 'bar',
      data: [120, 200, 150, 80, 170],
      itemStyle: { color: 'var(--accent)', borderRadius: [4, 4, 0, 0] },
      barWidth: '40%',
    }]
  }
})
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
