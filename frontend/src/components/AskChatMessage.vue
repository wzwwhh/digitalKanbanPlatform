<template>
  <div class="ai-message">
    <!-- 步骤指示器 -->
    <div class="steps" v-if="msg.steps.length">
      <div
        v-for="(step, i) in msg.steps"
        :key="i"
        class="step-item"
        :class="step.status"
      >
        <span class="step-icon">
          <template v-if="step.status === 'done'">✅</template>
          <template v-else><span class="spinner"></span></template>
        </span>
        <span class="step-text">{{ step.detail }}</span>
      </div>
    </div>

    <!-- 查询方案卡片 -->
    <div class="query-cards" v-if="msg.queries.length">
      <div v-for="(q, i) in msg.queries" :key="i" class="query-card">
        <div class="query-header">
          <span class="query-icon">🔍</span>
          <span class="query-ds">{{ q.dsName }}</span>
          <span class="query-desc">{{ q.description }}</span>
        </div>
        <div class="query-sql" v-if="q.sql">
          <code>{{ q.sql }}</code>
        </div>
      </div>
    </div>

    <!-- 数据表格 -->
    <div v-for="(table, i) in msg.tables" :key="'t'+i" class="data-table-wrap">
      <div class="table-header-bar">
        <span class="table-label">📋 {{ table.dsName }}</span>
        <span class="table-count">{{ table.total }} 条数据</span>
        <button
          v-if="table.rows.length > 5"
          class="table-toggle"
          @click="table._expanded = !table._expanded"
        >{{ table._expanded ? '收起' : '展开全部' }}</button>
      </div>
      <div class="table-scroll" :class="{ expanded: table._expanded }">
        <table>
          <thead>
            <tr>
              <th v-for="col in table.columns" :key="col">{{ col }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, ri) in displayRows(table)" :key="ri">
              <td v-for="col in table.columns" :key="col">{{ formatCell(row[col]) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- AI 文字分析 -->
    <div class="ai-text" v-if="msg.text">
      <div class="text-content" v-html="renderMarkdown(msg.text)"></div>
      <span v-if="!msg.done" class="cursor-blink">▍</span>
    </div>

    <!-- KPI 指标卡 -->
    <div class="kpi-row" v-if="msg.kpi && msg.kpi.length">
      <div v-for="(item, i) in msg.kpi" :key="i" class="kpi-card">
        <div class="kpi-label">{{ item.label }}</div>
        <div class="kpi-value">
          {{ item.value }}
          <span class="kpi-unit" v-if="item.unit">{{ item.unit }}</span>
        </div>
        <div class="kpi-change" v-if="item.change" :class="item.trend">
          <span class="trend-arrow">{{ item.trend === 'up' ? '↑' : item.trend === 'down' ? '↓' : '→' }}</span>
          {{ item.change }}
        </div>
      </div>
    </div>

    <!-- ECharts 图表 -->
    <div class="chart-block" v-if="msg.chart && msg.chart.echartsOption">
      <div class="chart-title-bar">
        <span class="chart-icon-label">📊</span>
        <span>{{ msg.chart.title || '数据可视化' }}</span>
      </div>
      <div class="chart-container">
        <v-chart class="inline-chart" :option="msg.chart.echartsOption" autoresize />
      </div>
    </div>

    <!-- 添加到看板 -->
    <div class="action-bar" v-if="msg.done && msg.widgetConfig">
      <button class="add-btn" @click="$emit('addToDashboard', msg.widgetConfig)">
        ✨ 添加到看板
      </button>
    </div>

    <!-- 错误信息 -->
    <div class="error-block" v-if="msg.error">
      <span class="error-icon">⚠️</span>
      {{ msg.error }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart, RadarChart, GaugeChart, ScatterChart } from 'echarts/charts'
import {
  GridComponent, TooltipComponent, LegendComponent,
  TitleComponent, DatasetComponent, VisualMapComponent
} from 'echarts/components'

use([
  CanvasRenderer,
  LineChart, BarChart, PieChart, RadarChart, GaugeChart, ScatterChart,
  GridComponent, TooltipComponent, LegendComponent,
  TitleComponent, DatasetComponent, VisualMapComponent
])

const props = defineProps({
  msg: { type: Object, required: true }
})

defineEmits(['addToDashboard'])

function displayRows(table) {
  if (table._expanded) return table.rows
  return table.rows.slice(0, 5)
}

function formatCell(value) {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'number') {
    if (Number.isInteger(value)) return value.toLocaleString()
    return value.toLocaleString(undefined, { maximumFractionDigits: 2 })
  }
  return String(value)
}

function renderMarkdown(text) {
  if (!text) return ''
  let html = text
    // 转义 HTML
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // 加粗
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // 列表项
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    // 换行
    .replace(/\n/g, '<br>')
  // 包裹连续 li
  html = html.replace(/((?:<li>.*?<\/li><br>?)+)/g, '<ul>$1</ul>')
  html = html.replace(/<br><\/ul>/g, '</ul>')
  html = html.replace(/<ul><br>/g, '<ul>')
  return html
}
</script>

<style scoped>
.ai-message {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 步骤 */
.steps {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted, #4a5578);
  transition: color 0.3s;
}

.step-item.done {
  color: var(--text-secondary, #8892b0);
}

.step-item.loading {
  color: var(--accent, #00d4ff);
}

.step-icon {
  font-size: 14px;
  width: 18px;
  text-align: center;
  flex-shrink: 0;
}

.spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(0, 212, 255, 0.3);
  border-top-color: var(--accent, #00d4ff);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 查询卡片 */
.query-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.query-card {
  padding: 10px 14px;
  background: rgba(0, 212, 255, 0.05);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 8px;
}

.query-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  margin-bottom: 6px;
}

.query-icon { font-size: 14px; }

.query-ds {
  font-weight: 600;
  color: var(--text-primary, #e0e6ff);
}

.query-desc {
  color: var(--text-muted, #4a5578);
  font-size: 12px;
}

.query-sql {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
  padding: 6px 10px;
  overflow-x: auto;
}

.query-sql code {
  font-size: 11px;
  color: var(--accent, #00d4ff);
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  white-space: pre-wrap;
  word-break: break-all;
}

/* 数据表格 */
.data-table-wrap {
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 10px;
  overflow: hidden;
}

.table-header-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  background: rgba(123, 97, 255, 0.06);
  border-bottom: 1px solid var(--border-color, #2a3560);
}

.table-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary, #e0e6ff);
}

.table-count {
  font-size: 11px;
  color: var(--text-muted, #4a5578);
  margin-left: auto;
}

.table-toggle {
  font-size: 11px;
  color: var(--accent, #00d4ff);
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 6px;
}

.table-toggle:hover { text-decoration: underline; }

.table-scroll {
  max-height: 220px;
  overflow: auto;
  transition: max-height 0.3s;
}

.table-scroll.expanded {
  max-height: 500px;
}

.table-scroll table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.table-scroll th,
.table-scroll td {
  padding: 6px 12px;
  text-align: left;
  white-space: nowrap;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.table-scroll th {
  position: sticky;
  top: 0;
  background: var(--bg-secondary, #131837);
  color: var(--text-muted, #4a5578);
  font-weight: 500;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.table-scroll td {
  color: var(--text-secondary, #8892b0);
}

.table-scroll tbody tr:nth-child(even) td {
  background: rgba(255, 255, 255, 0.015);
}

.table-scroll tbody tr:hover td {
  background: rgba(0, 212, 255, 0.04);
}

/* AI 文字 */
.ai-text {
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary, #e0e6ff);
  padding: 4px 0;
}

.ai-text :deep(strong) {
  color: var(--accent, #00d4ff);
  font-weight: 600;
}

.ai-text :deep(ul) {
  padding-left: 18px;
  margin: 6px 0;
}

.ai-text :deep(li) {
  margin: 2px 0;
  color: var(--text-secondary, #8892b0);
}

.cursor-blink {
  display: inline;
  color: var(--accent, #00d4ff);
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* KPI 卡片 */
.kpi-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.kpi-card {
  flex: 1;
  min-width: 120px;
  max-width: 200px;
  padding: 12px 16px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(123, 97, 255, 0.1), rgba(0, 212, 255, 0.06));
  border: 1px solid rgba(123, 97, 255, 0.2);
}

.kpi-label {
  font-size: 11px;
  color: var(--text-muted, #4a5578);
  margin-bottom: 4px;
}

.kpi-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary, #e0e6ff);
  line-height: 1.2;
}

.kpi-unit {
  font-size: 12px;
  font-weight: 400;
  color: var(--text-muted, #4a5578);
  margin-left: 2px;
}

.kpi-change {
  font-size: 12px;
  margin-top: 4px;
}

.kpi-change.up { color: #36d399; }
.kpi-change.down { color: #f87272; }
.kpi-change.flat { color: var(--text-muted, #4a5578); }

.trend-arrow { margin-right: 2px; }

/* 图表 */
.chart-block {
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 10px;
  overflow: hidden;
}

.chart-title-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(0, 212, 255, 0.04);
  border-bottom: 1px solid var(--border-color, #2a3560);
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary, #e0e6ff);
}

.chart-icon-label { font-size: 16px; }

.chart-container {
  padding: 12px;
}

.inline-chart {
  width: 100%;
  height: 280px;
}

/* 操作栏 */
.action-bar {
  padding-top: 4px;
}

.add-btn {
  padding: 8px 20px;
  border-radius: 8px;
  border: none;
  background: linear-gradient(135deg, #7b61ff, #00d4ff);
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.15s;
}

.add-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

/* 错误 */
.error-block {
  padding: 10px 14px;
  background: rgba(248, 114, 114, 0.08);
  border: 1px solid rgba(248, 114, 114, 0.25);
  border-radius: 8px;
  font-size: 13px;
  color: #f87272;
}

.error-icon { margin-right: 6px; }
</style>
