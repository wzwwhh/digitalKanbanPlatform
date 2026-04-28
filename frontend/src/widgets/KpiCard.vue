<template>
  <div class="kpi-card" :style="cardStyle">
    <div class="kpi-title">{{ props.props.title || 'KPI 指标' }}</div>
    <div class="kpi-value-row">
      <span class="kpi-value">{{ displayValue }}</span>
      <span v-if="props.props.unit" class="kpi-unit">{{ props.props.unit }}</span>
    </div>
    <div v-if="props.props.trend && props.props.trend !== 'flat'" class="kpi-trend" :class="`trend-${props.props.trend}`">
      <span class="trend-icon">{{ props.props.trend === 'up' ? '↑' : '↓' }}</span>
      <span class="trend-text">{{ props.props.trend === 'up' ? '上升' : '下降' }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import { fetchWidgetData } from '../services/dataFetcher'
import { useProjectStore } from '../stores/project'

const props = defineProps({
  widget: { type: Object, default: () => ({}) },
  props: {
    type: Object,
    default: () => ({
      title: 'KPI 指标',
      value: '0',
      unit: '',
      trend: 'flat',
      color: '',
    })
  }
})

const projectStore = useProjectStore()
const liveValue = ref(null)

async function loadData() {
  if (!props.widget?.dataSource?.sourceId) return
  const ds = projectStore.currentProject?.dataSources || []
  const result = await fetchWidgetData(props.widget.dataSource, ds)
  if (!result) return
  const mapping = props.widget.dataSource.mapping || {}
  if (mapping.value) {
    // KPI 数据通常是单个对象（如 /api/mock/kpi）
    const raw = result.raw
    if (raw && !Array.isArray(raw)) {
      liveValue.value = raw[mapping.value]
    } else if (result.rows?.length > 0) {
      liveValue.value = result.rows[0][mapping.value]
    }
  }
}

onMounted(loadData)
watch(() => props.widget?.dataSource, loadData, { deep: true })

const displayValue = computed(() => {
  if (liveValue.value !== null && liveValue.value !== undefined) {
    const v = liveValue.value
    if (typeof v === 'number') {
      return v >= 1000 ? v.toLocaleString() : v.toString()
    }
    return String(v)
  }
  return props.props.value ?? '0'
})

const cardStyle = computed(() => ({
  borderColor: props.props.color || 'var(--border-color)',
}))
</script>

<style scoped>
.kpi-card {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 16px;
  background: var(--bg-card);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  box-sizing: border-box;
}

.kpi-title {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.kpi-value-row {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.kpi-value {
  font-size: 36px;
  font-weight: 700;
  color: var(--accent);
  font-variant-numeric: tabular-nums;
}

.kpi-unit {
  font-size: 14px;
  color: var(--text-secondary);
}

.kpi-trend {
  margin-top: 8px;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.trend-up {
  color: var(--accent-success);
}

.trend-down {
  color: var(--accent-danger);
}
</style>
