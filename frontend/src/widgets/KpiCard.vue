<template>
  <div class="kpi-card">
    <div class="kpi-title">{{ props.title }}</div>
    <div class="kpi-value-row">
      <span class="kpi-value">{{ props.value }}</span>
      <span v-if="props.unit" class="kpi-unit">{{ props.unit }}</span>
    </div>
    <div v-if="props.trend && props.trend !== 'flat'" class="kpi-trend" :class="`trend-${props.trend}`">
      <span class="trend-icon">{{ props.trend === 'up' ? '↑' : '↓' }}</span>
      <span class="trend-text">{{ props.trend === 'up' ? '上升' : '下降' }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
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
