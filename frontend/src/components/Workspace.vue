<template>
  <div class="workspace" @click.self="dashboardStore.deselectAll()">
    <div class="canvas" :style="canvasStyle">
      <!-- 网格背景 -->
      <div class="grid-bg"></div>

      <!-- 渲染所有组件 -->
      <WidgetWrapper
        v-for="widget in dashboardStore.widgets"
        :key="widget.id"
        :widget="widget"
        :selected="widget.id === dashboardStore.selectedId"
        @select="dashboardStore.selectWidget(widget.id)"
        @move="onWidgetMove(widget.id, $event)"
        @resize="onWidgetResize(widget.id, $event)"
      />

      <!-- 空画布提示 -->
      <div v-if="dashboardStore.widgets.length === 0" class="empty-hint">
        <div class="empty-icon">🎨</div>
        <div class="empty-text">画布为空</div>
        <div class="empty-sub">从左侧素材库拖入组件，或使用 AI 生成看板</div>

        <!-- 临时：快速添加示例组件 -->
        <button class="btn-demo" @click="addDemoWidgets">🚀 添加示例组件</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useDashboardStore } from '../stores/dashboard'
import { executeCommand, createCommand, CommandType } from '../core/command'
import WidgetWrapper from '../widgets/WidgetWrapper.vue'

const dashboardStore = useDashboardStore()

const canvasStyle = computed(() => ({
  width: '1920px',
  height: '1080px',
}))

function onWidgetMove(id, position) {
  executeCommand(createCommand(CommandType.MOVE_WIDGET, { id, position }))
}

function onWidgetResize(id, size) {
  executeCommand(createCommand(CommandType.RESIZE_WIDGET, { id, size }))
}

function addDemoWidgets() {
  const demoWidgets = [
    {
      type: 'text',
      props: { content: '电商销售看板', fontSize: 28, align: 'center', color: '' },
      position: { x: 660, y: 20 },
      size: { w: 600, h: 60 },
    },
    {
      type: 'kpi',
      props: { title: '今日订单', value: '1,234', unit: '单', trend: 'up' },
      position: { x: 50, y: 100 },
      size: { w: 280, h: 160 },
    },
    {
      type: 'kpi',
      props: { title: '今日营收', value: '¥89,560', unit: '', trend: 'up' },
      position: { x: 350, y: 100 },
      size: { w: 280, h: 160 },
    },
    {
      type: 'kpi',
      props: { title: '转化率', value: '3.2%', unit: '', trend: 'down' },
      position: { x: 650, y: 100 },
      size: { w: 280, h: 160 },
    },
    {
      type: 'line',
      props: { title: '销售趋势', smooth: true, area: true },
      position: { x: 50, y: 290 },
      size: { w: 580, h: 320 },
    },
    {
      type: 'bar',
      props: { title: '产品销量对比', stack: false, horizontal: false },
      position: { x: 650, y: 290 },
      size: { w: 450, h: 320 },
    },
    {
      type: 'pie',
      props: { title: '流量来源', donut: true, showLabel: true },
      position: { x: 1120, y: 290 },
      size: { w: 320, h: 320 },
    },
  ]

  const batchCommands = demoWidgets.map(w =>
    createCommand(CommandType.ADD_WIDGET, w)
  )

  executeCommand(createCommand(CommandType.BATCH, { commands: batchCommands }))
}
</script>

<style scoped>
.workspace {
  width: 100%;
  height: 100%;
  overflow: auto;
  background: var(--bg-primary);
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  padding: 20px;
}

.canvas {
  position: relative;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  flex-shrink: 0;
  overflow: hidden;
}

.grid-bg {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(var(--border-color) 1px, transparent 1px),
    linear-gradient(90deg, var(--border-color) 1px, transparent 1px);
  background-size: 20px 20px;
  opacity: 0.3;
  pointer-events: none;
}

.empty-hint {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-text {
  font-size: 20px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.empty-sub {
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 24px;
}

.btn-demo {
  padding: 10px 24px;
  background: linear-gradient(135deg, var(--accent), var(--accent-secondary));
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-demo:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 212, 255, 0.3);
}
</style>
