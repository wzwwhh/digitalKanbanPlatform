<template>
  <div class="ranking-widget">
    <div class="ranking-title">{{ props.props.title || '排行榜' }}</div>
    <div class="ranking-list">
      <div v-for="(item, idx) in displayItems" :key="idx" class="ranking-item">
        <div class="rank-index" :class="{ gold: idx === 0, silver: idx === 1, bronze: idx === 2 }">{{ idx + 1 }}</div>
        <div class="rank-name">{{ item.name }}</div>
        <div class="rank-bar-wrap">
          <div class="rank-bar" :style="{ width: barWidth(item.value) }"></div>
        </div>
        <div class="rank-value">{{ formatValue(item.value) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import { fetchWidgetData } from '../services/dataFetcher'
import { useProjectStore } from '../stores/project'

const props = defineProps({
  widget: { type: Object, default: () => ({}) },
  props: { type: Object, default: () => ({}) },
})

const projectStore = useProjectStore()
const liveItems = ref(null)

// 从数据源加载
async function loadData() {
  if (!props.widget?.dataSource?.sourceId) return
  const ds = projectStore.currentProject?.dataSources || []
  const result = await fetchWidgetData(props.widget.dataSource, ds)
  if (!result?.rows) return

  const mapping = props.widget.dataSource.mapping || {}
  if (mapping.name && mapping.value) {
    liveItems.value = result.rows.map(r => ({
      name: r[mapping.name],
      value: Number(r[mapping.value]) || 0,
    })).sort((a, b) => b.value - a.value)
  }
}

onMounted(loadData)
watch(() => props.widget?.dataSource, loadData, { deep: true })

const displayItems = computed(() => {
  if (liveItems.value) return liveItems.value
  return props.props.items?.length ? props.props.items : [
    { name: '示例A', value: 120 },
    { name: '示例B', value: 86 },
    { name: '示例C', value: 65 },
    { name: '示例D', value: 42 },
    { name: '示例E', value: 28 },
  ]
})

const maxValue = computed(() => {
  const vals = displayItems.value.map(i => Number(i.value) || 0)
  return Math.max(...vals, 1)
})

function barWidth(val) {
  return `${(Number(val) / maxValue.value) * 100}%`
}

function formatValue(val) {
  const n = Number(val)
  if (n >= 10000) return `${(n / 10000).toFixed(1)}万`
  return n.toLocaleString()
}
</script>

<style scoped>
.ranking-widget {
  width: 100%; height: 100%;
  display: flex; flex-direction: column;
  background: var(--bg-card);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  box-sizing: border-box;
  padding: 12px;
}

.ranking-title {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow: auto;
  flex: 1;
}

.ranking-item {
  display: grid;
  grid-template-columns: 28px 80px 1fr auto;
  gap: 8px;
  align-items: center;
  padding: 6px 10px;
  background: var(--bg-tertiary);
  border-radius: 6px;
  transition: background 0.15s;
}

.ranking-item:hover {
  background: rgba(0, 212, 255, 0.06);
}

.rank-index {
  font-weight: 700;
  text-align: center;
  font-size: 13px;
  color: var(--text-muted);
}

.rank-index.gold { color: #ffd700; }
.rank-index.silver { color: #c0c0c0; }
.rank-index.bronze { color: #cd7f32; }

.rank-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}

.rank-bar-wrap {
  height: 8px;
  background: rgba(0, 212, 255, 0.08);
  border-radius: 4px;
  overflow: hidden;
}

.rank-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--accent, #00d4ff), rgba(123, 97, 255, 0.8));
  border-radius: 4px;
  transition: width 0.5s ease;
}

.rank-value {
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
  font-size: 12px;
  min-width: 40px;
  text-align: right;
}
</style>
