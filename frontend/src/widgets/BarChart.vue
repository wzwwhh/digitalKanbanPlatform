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
import { BarChart as EBarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { fetchWidgetData } from '../services/dataFetcher'
import { useProjectStore } from '../stores/project'

use([CanvasRenderer, EBarChart, GridComponent, TooltipComponent])

const props = defineProps({
  widget: { type: Object, default: () => ({}) },
  props: {
    type: Object,
    default: () => ({
      title: '柱状图',
      stack: false,
      horizontal: false,
      categories: [],
      values: [],
    })
  }
})

const projectStore = useProjectStore()
const liveCategories = ref(null)
const liveValues = ref(null)

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
  const categoryData = liveCategories.value
    || (props.props.categories?.length ? props.props.categories : null)
    || ['产品A', '产品B', '产品C', '产品D', '产品E']
  const valueData = liveValues.value
    || (props.props.values?.length ? props.props.values : null)
    || [120, 200, 150, 80, 170]

  const categoryAxis = {
    type: 'category',
    data: categoryData,
    axisLine: { lineStyle: { color: 'var(--text-muted)' } },
    axisLabel: { color: 'var(--text-secondary)' },
  }
  const valueAxis = {
    type: 'value',
    splitLine: { lineStyle: { color: 'var(--border-color)', type: 'dashed' } },
    axisLabel: { color: 'var(--text-secondary)' },
  }

    const isHor = props.props.horizontal
    const baseColor = props.props.color || '#00d4ff'
    
    return {
      tooltip: { trigger: 'axis' },
      grid: { top: 10, right: 16, bottom: 24, left: 40 },
      xAxis: isHor ? valueAxis : categoryAxis,
      yAxis: isHor ? categoryAxis : valueAxis,
      series: [{
        type: 'bar',
        data: valueData,
        itemStyle: { 
          color: {
            type: 'linear',
            x: 0, y: 0, 
            x2: isHor ? 1 : 0, y2: isHor ? 0 : 1,
            colorStops: [
              { offset: 0, color: baseColor },
              { offset: 1, color: baseColor.startsWith('#') ? baseColor + '1A' : 'rgba(0, 212, 255, 0.1)' } // 10% opacity
            ]
          },
          borderRadius: isHor ? [0, 4, 4, 0] : [4, 4, 0, 0] 
        },
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
