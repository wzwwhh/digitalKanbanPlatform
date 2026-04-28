<template>
  <div class="numberflip-widget">
    <div class="numberflip-title">{{ p.props.title || '数字翻牌' }}</div>
    <div class="numberflip-row">
      <span v-if="p.props.prefix" class="flip-affix">{{ p.props.prefix }}</span>
      <span class="flip-digits">
        <span v-for="(digit, i) in digits" :key="i" class="flip-cell" :class="{ sep: digit === ',' }">
          <span class="flip-inner" :style="{ transform: `translateY(-${getOffset(digit)}%)` }">
            <span v-for="n in 10" :key="n" class="flip-num">{{ n - 1 }}</span>
          </span>
          <span v-if="digit === ','" class="flip-comma">,</span>
        </span>
      </span>
      <span v-if="p.props.suffix" class="flip-affix">{{ p.props.suffix }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import { fetchWidgetData } from '../services/dataFetcher'
import { useProjectStore } from '../stores/project'

const p = defineProps({
  widget: { type: Object, default: () => ({}) },
  props: { type: Object, default: () => ({}) },
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
      liveValue.value = raw[mapping.value]
    } else if (result.rows?.length > 0) {
      liveValue.value = result.rows[0][mapping.value]
    }
  }
}

onMounted(loadData)
watch(() => p.widget?.dataSource, loadData, { deep: true })

const displayValue = computed(() => {
  if (liveValue.value !== null && liveValue.value !== undefined) {
    const v = Number(liveValue.value)
    return isNaN(v) ? String(liveValue.value) : v.toLocaleString()
  }
  const v = Number(p.props.value)
  return isNaN(v) ? String(p.props.value || '0') : v.toLocaleString()
})

const digits = computed(() => displayValue.value.split(''))

function getOffset(digit) {
  const n = parseInt(digit)
  return isNaN(n) ? 0 : n * 10
}
</script>

<style scoped>
.numberflip-widget {
  width: 100%; height: 100%;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  background: var(--bg-card);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 12px;
  box-sizing: border-box;
}

.numberflip-title {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 10px;
}

.numberflip-row {
  display: flex;
  align-items: center;
  gap: 2px;
}

.flip-affix {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0 2px;
}

.flip-digits {
  display: flex;
  gap: 2px;
}

.flip-cell {
  width: 28px;
  height: 40px;
  overflow: hidden;
  background: var(--bg-tertiary, #1a2045);
  border-radius: 4px;
  position: relative;
}

.flip-cell.sep {
  width: 10px;
  background: none;
}

.flip-inner {
  display: flex;
  flex-direction: column;
  transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.flip-num {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 40px;
  font-size: 26px;
  font-weight: 700;
  color: var(--accent, #00d4ff);
  font-variant-numeric: tabular-nums;
}

.flip-comma {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: var(--text-muted);
}
</style>
