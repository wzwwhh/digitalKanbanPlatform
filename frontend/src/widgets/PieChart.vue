<template>
  <div class="chart-widget">
    <div class="chart-title">{{ p.props.title }}</div>
    <v-chart class="chart" :option="chartOption" autoresize />
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart as EPieChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import { fetchWidgetData } from '../services/dataFetcher'
import { useProjectStore } from '../stores/project'

use([CanvasRenderer, EPieChart, TooltipComponent, LegendComponent])

const p = defineProps({
  widget: { type: Object, default: () => ({}) },
  props: {
    type: Object,
    default: () => ({
      title: '饼图',
      donut: false,
      showLabel: true,
    })
  }
})

const projectStore = useProjectStore()
const liveData = ref(null)

async function loadData() {
  if (!p.widget?.dataSource?.sourceId) return
  const ds = projectStore.currentProject?.dataSources || []
  const result = await fetchWidgetData(p.widget.dataSource, ds)
  if (!result?.rows) return
  const mapping = p.widget.dataSource.mapping || {}
  // 饼图需要 name + value
  if (mapping.name && mapping.value) {
    liveData.value = result.rows.map(r => ({
      name: r[mapping.name],
      value: r[mapping.value],
    }))
  }
}

onMounted(loadData)
watch(() => p.widget?.dataSource, loadData, { deep: true })

const chartOption = computed(() => {
  const data = liveData.value
    || (p.props.data?.length ? p.props.data : null)
    || [
      { value: 335, name: '直接访问' },
      { value: 234, name: '邮件营销' },
      { value: 154, name: '联盟广告' },
      { value: 135, name: '视频广告' },
      { value: 148, name: '搜索引擎' },
    ]

  return {
    tooltip: { trigger: 'item' },
    legend: {
      bottom: 0,
      textStyle: { color: 'var(--text-secondary)' },
    },
    series: [{
      type: 'pie',
      radius: p.props.donut ? ['40%', '70%'] : '70%',
      center: ['50%', '45%'],
      data,
      label: {
        show: p.props.showLabel,
        color: 'var(--text-secondary)',
      },
      emphasis: {
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' }
      }
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
