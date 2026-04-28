<template>
  <div class="chart-widget">
    <div class="chart-title">{{ p.props.title || '仪表盘' }}</div>
    <v-chart class="chart" :option="chartOption" autoresize />
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { GaugeChart as EGaugeChart } from 'echarts/charts'
import { fetchWidgetData } from '../services/dataFetcher'
import { useProjectStore } from '../stores/project'

use([CanvasRenderer, EGaugeChart])

const p = defineProps({
  widget: { type: Object, default: () => ({}) },
  props: {
    type: Object,
    default: () => ({
      title: '仪表盘',
      value: 50,
      min: 0,
      max: 100,
    })
  },
})

const projectStore = useProjectStore()
const liveValue = ref(null)

async function loadData() {
  if (!p.widget?.dataSource?.sourceId) return
  const ds = projectStore.currentProject?.dataSources || []
  const result = await fetchWidgetData(p.widget.dataSource, ds)
  if (!result) return
  const mapping = p.widget.dataSource.mapping || {}
  if (mapping.value) {
    const raw = result.raw
    if (raw && !Array.isArray(raw)) {
      liveValue.value = Number(raw[mapping.value]) || 0
    } else if (result.rows?.length > 0) {
      liveValue.value = Number(result.rows[0][mapping.value]) || 0
    }
  }
}

onMounted(loadData)
watch(() => p.widget?.dataSource, loadData, { deep: true })

const displayValue = computed(() => {
  if (liveValue.value !== null) return liveValue.value
  return Number(p.props.value) || 0
})

const chartOption = computed(() => {
  const min = Number(p.props.min) || 0
  const max = Number(p.props.max) || 100

  return {
    series: [{
      type: 'gauge',
      min,
      max,
      progress: { show: true, width: 12 },
      axisLine: {
        lineStyle: { width: 12, color: [[1, 'rgba(0,212,255,0.15)']] },
      },
      axisTick: { show: false },
      splitLine: {
        length: 8,
        lineStyle: { width: 2, color: '#4a5578' },
      },
      axisLabel: {
        distance: 18,
        color: '#8892b0',
        fontSize: 10,
      },
      pointer: {
        icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z',
        length: '60%',
        width: 6,
        itemStyle: { color: '#00d4ff' },
      },
      anchor: {
        show: true,
        size: 16,
        itemStyle: { borderWidth: 2, borderColor: '#00d4ff', color: '#161d42' },
      },
      title: { show: false },
      detail: {
        valueAnimation: true,
        fontSize: 22,
        fontWeight: 700,
        color: '#00d4ff',
        offsetCenter: [0, '70%'],
        formatter: '{value}',
      },
      data: [{ value: displayValue.value }],
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
