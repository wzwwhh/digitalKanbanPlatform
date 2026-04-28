<template>
  <div class="table-widget">
    <div class="table-title">{{ props.props.title || '数据表格' }}</div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th v-for="col in displayColumns" :key="col">{{ col }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in displayRows" :key="idx">
            <td v-for="col in displayColumns" :key="col">{{ row?.[col] ?? '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="table-footer" v-if="displayRows.length > 0">
      <span>共 {{ displayRows.length }} 条</span>
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
const liveData = ref(null)

// 从数据源加载
async function loadData() {
  if (!props.widget?.dataSource?.sourceId) return
  const ds = projectStore.currentProject?.dataSources || []
  const result = await fetchWidgetData(props.widget.dataSource, ds)
  if (!result?.rows) return
  liveData.value = result.rows
}

onMounted(loadData)
watch(() => props.widget?.dataSource, loadData, { deep: true })

const displayRows = computed(() => {
  if (liveData.value) return liveData.value
  return props.props.rows?.length ? props.props.rows : [
    { 名称: '示例A', 数值: 120 },
    { 名称: '示例B', 数值: 86 },
  ]
})

const displayColumns = computed(() => {
  // 优先用 props 中指定的列名
  if (props.props.columns?.length) return props.props.columns
  // 否则从数据行中提取
  if (displayRows.value.length > 0) {
    return Object.keys(displayRows.value[0])
  }
  return ['名称', '数值']
})
</script>

<style scoped>
.table-widget {
  width: 100%; height: 100%;
  display: flex; flex-direction: column;
  background: var(--bg-card);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  box-sizing: border-box;
  padding: 12px;
}

.table-title {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.table-wrap {
  flex: 1;
  overflow: auto;
}

.table-wrap table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.table-wrap th,
.table-wrap td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--border-color);
  text-align: left;
  white-space: nowrap;
}

.table-wrap th {
  color: var(--text-secondary);
  position: sticky;
  top: 0;
  background: var(--bg-card);
  font-weight: 500;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.table-wrap tr:hover td {
  background: rgba(0, 212, 255, 0.04);
}

.table-footer {
  padding-top: 8px;
  font-size: 11px;
  color: var(--text-muted);
  text-align: right;
}
</style>
