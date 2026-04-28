<template>
  <div class="chart-widget">
    <div class="chart-title">{{ props.props.title }}</div>
    <v-chart class="chart" :option="chartOption" autoresize />
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart as ELineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { fetchWidgetData } from '../services/dataFetcher'
import { useProjectStore } from '../stores/project'

use([CanvasRenderer, ELineChart, GridComponent, TooltipComponent, LegendComponent])

const props = defineProps({
  props: {
    type: Object,
    default: () => ({
      title: '折线图',
      smooth: true,
      area: false,
      categories: [],
      values: [],
    })
  },
  widget: {
    type: Object,
    default: null,
  }
})

const projectStore = useProjectStore()
const liveCategories = ref(null)
const liveValues = ref(null)

// 获取真实数据
async function loadData() {
  if (!props.widget?.dataSource?.sourceId) return
  const ds = projectStore.currentProject?.dataSources || []
  const result = await fetchWidgetData(props.widget.dataSource, ds)
  if (!result?.rows) return

  const mapping = props.widget.dataSource.mapping || {}
  if (mapping.x && mapping.y) {
    liveCategories.value = result.rows.map(r => r[mapping.x])
    liveValues.value = result.rows.map(r => r[mapping.y])
  }
}

onMounted(loadData)
watch(() => props.widget?.dataSource, loadData, { deep: true })

const chartOption = computed(() => {
  const categories = liveCategories.value
    || (props.props.categories?.length ? props.props.categories : null)
    || ['1月', '2月', '3月', '4月', '5月', '6月']
  const values = liveValues.value
    || (props.props.values?.length ? props.props.values : null)
    || [820, 932, 901, 1234, 1090, 1330]

  return {
    tooltip: { trigger: 'axis' },
    grid: { top: 10, right: 16, bottom: 24, left: 40 },
    xAxis: {
      type: 'category',
      data: categories,
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
      data: values,
      smooth: props.props.smooth,
      areaStyle: props.props.area ? { opacity: 0.15 } : undefined,
      lineStyle: { color: 'var(--accent)', width: 2 },
      itemStyle: { color: 'var(--accent)' },
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
