<template>
  <div class="workspace" @click.self="dashboardStore.deselectAll()">
    <div class="workspace-toolbar">
      <div class="toolbar-group">
        <button class="zoom-btn" @click="zoomOut">-</button>
        <span class="zoom-label">{{ Math.round(scale * 100) }}%</span>
        <button class="zoom-btn" @click="zoomIn">+</button>
        <button class="zoom-btn zoom-fit" @click="fitCanvas">⊡ 自适应</button>
      </div>

      <div class="toolbar-divider"></div>

      <select 
        class="board-theme-select" 
        v-model="internalBoardTheme" 
        title="画布主题（独立于系统）"
      >
        <option :value="null">🎨 跟随系统</option>
        <option v-for="t in themeStore.allThemes" :key="t.id" :value="t.id">{{ t.label }}</option>
      </select>

      <div class="toolbar-group">
        <button class="toolbar-btn" @click="$refs.bgImageInput.click()" title="上传本地图片作为大屏底图">
          🖼️ 设置底图
        </button>
        <button v-if="bgImage" class="toolbar-btn danger-text" @click="$emit('update:bgImage', null)" title="清除背景图">
          ❌ 清除
        </button>
        <input type="file" ref="bgImageInput" style="display: none" accept="image/*" @change="onBgImageSelected">
      </div>

      <div class="toolbar-divider"></div>

      <div class="toolbar-group action-group">
        <button class="toolbar-btn" @click="$emit('open-ds')" title="数据源管理">
          🗄️ 数据源
        </button>
        <button 
          class="toolbar-btn btn-layout-fast" 
          @click="$emit('auto-layout', 'fast')" 
          :disabled="layoutLoading || dashboardStore.widgets.length === 0"
        >
          {{ layoutLoading === 'fast' ? '⏳...' : '⚡ 快速排版' }}
        </button>
        <button 
          class="toolbar-btn btn-layout-ai" 
          @click="$emit('auto-layout', 'ai')" 
          :disabled="layoutLoading || dashboardStore.widgets.length === 0"
        >
          {{ layoutLoading === 'ai' ? '⏳...' : '✨ AI排版' }}
        </button>
      </div>
    </div>
    <div class="canvas-shell" ref="shellRef" @wheel.prevent="onWheel">
      <div class="canvas" :style="[canvasStyle, bgImageStyle]">
        <div class="grid-bg"></div>

        <WidgetWrapper
          v-for="widget in dashboardStore.widgets"
          :key="widget.id"
          :widget="widget"
          :selected="widget.id === dashboardStore.selectedId"
          :scale="scale"
          @select="dashboardStore.selectWidget(widget.id)"
          @move="onWidgetMove(widget.id, $event)"
          @resize="onWidgetResize(widget.id, $event)"
          @contextmenu.prevent="openContextMenu($event, widget)"
        />

        <div v-if="dashboardStore.widgets.length === 0" class="empty-hint">
          <div class="empty-icon">🎨</div>
          <div class="empty-text">画布为空</div>
          <div class="empty-sub">从左侧点击组件添加，或使用 AI 生成看板</div>
          <button class="btn-demo" @click="addDemoWidgets">🚀 添加示例组件</button>
        </div>
      </div>
    </div>

    <!-- 右键菜单 -->
    <div v-if="ctxMenu.show" class="context-menu" :style="ctxMenuStyle" @click.stop>
      <button class="ctx-item" @click="ctxDuplicate">📋 复制组件</button>
      <button class="ctx-item" @click="ctxMoveTop">⬆ 置顶</button>
      <button class="ctx-item" @click="ctxMoveBottom">⬇ 置底</button>
      <button class="ctx-item danger" @click="ctxDelete">🗑 删除</button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useDashboardStore } from '../stores/dashboard'
import { useThemeStore } from '../stores/theme'
import { executeCommand, createCommand, CommandType } from '../core/command'
import { getAllThemes } from '../core/registry'
import WidgetWrapper from '../widgets/WidgetWrapper.vue'

const props = defineProps({
  boardTheme: { type: String, default: null },
  bgImage: { type: String, default: null },
  layoutLoading: { type: String, default: '' }
})

const emit = defineEmits(['update:boardTheme', 'update:bgImage', 'open-ds', 'auto-layout'])

const internalBoardTheme = computed({
  get: () => props.boardTheme,
  set: (val) => emit('update:boardTheme', val)
})

const dashboardStore = useDashboardStore()
const themeStore = useThemeStore()
const shellRef = ref(null)
const scale = ref(1)
const minScale = 0.35
const maxScale = 1.4

const canvasStyle = computed(() => {
  return {
    width: '1920px',
    height: '1080px',
    transform: `scale(${scale.value})`,
    transformOrigin: 'top left',
  }
})

const bgImageStyle = computed(() => {
  if (!props.bgImage) return {}
  return {
    backgroundImage: `url(${props.bgImage})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundRepeat: 'no-repeat',
  }
})

const bgImageInput = ref(null)

function onBgImageSelected(e) {
  const file = e.target.files[0]
  if (!file) return
  
  const reader = new FileReader()
  reader.onload = (event) => {
    emit('update:bgImage', event.target.result)
  }
  reader.readAsDataURL(file)
  
  // Reset input so the same file can be selected again if needed
  e.target.value = ''
}

function zoomIn() {
  scale.value = Math.min(maxScale, +(scale.value + 0.1).toFixed(2))
}

function zoomOut() {
  scale.value = Math.max(minScale, +(scale.value - 0.1).toFixed(2))
}

function fitCanvas() {
  const shell = shellRef.value
  if (!shell) return
  const padding = 48
  const sx = (shell.clientWidth - padding) / 1920
  const sy = (shell.clientHeight - padding) / 1080
  scale.value = Math.max(minScale, Math.min(maxScale, Math.min(sx, sy)))
}

// 滚轮缩放
function onWheel(e) {
  const delta = e.deltaY > 0 ? -0.05 : 0.05
  scale.value = Math.max(minScale, Math.min(maxScale, +(scale.value + delta).toFixed(2)))
}

function onWidgetMove(id, position) {
  executeCommand(createCommand(CommandType.MOVE_WIDGET, { id, position }))
}

function onWidgetResize(id, size) {
  executeCommand(createCommand(CommandType.RESIZE_WIDGET, { id, size }))
}

// ===== 右键菜单 =====
const ctxMenu = ref({ show: false, x: 0, y: 0, widget: null })

const ctxMenuStyle = computed(() => ({
  left: `${ctxMenu.value.x}px`,
  top: `${ctxMenu.value.y}px`,
}))

function openContextMenu(e, widget) {
  dashboardStore.selectWidget(widget.id)
  ctxMenu.value = { show: true, x: e.clientX, y: e.clientY, widget }
}

function closeContextMenu() {
  ctxMenu.value = { show: false, x: 0, y: 0, widget: null }
}

function ctxDuplicate() {
  const w = ctxMenu.value.widget
  if (!w) return
  executeCommand(createCommand(CommandType.ADD_WIDGET, {
    type: w.type,
    props: JSON.parse(JSON.stringify(w.props)),
    position: { x: w.position.x + 30, y: w.position.y + 30 },
    size: { ...w.size },
    dataSource: w.dataSource ? JSON.parse(JSON.stringify(w.dataSource)) : undefined,
  }))
  closeContextMenu()
}

function ctxMoveTop() {
  const w = ctxMenu.value.widget
  if (!w) return
  // 将组件移到 widgets 数组末尾（最上层）
  const idx = dashboardStore.widgets.findIndex(i => i.id === w.id)
  if (idx >= 0 && idx < dashboardStore.widgets.length - 1) {
    const item = dashboardStore.widgets.splice(idx, 1)[0]
    dashboardStore.widgets.push(item)
  }
  closeContextMenu()
}

function ctxMoveBottom() {
  const w = ctxMenu.value.widget
  if (!w) return
  // 将组件移到 widgets 数组头部（最下层）
  const idx = dashboardStore.widgets.findIndex(i => i.id === w.id)
  if (idx > 0) {
    const item = dashboardStore.widgets.splice(idx, 1)[0]
    dashboardStore.widgets.unshift(item)
  }
  closeContextMenu()
}

function ctxDelete() {
  const w = ctxMenu.value.widget
  if (!w) return
  executeCommand(createCommand(CommandType.DELETE_WIDGET, { id: w.id }))
  closeContextMenu()
}

// 点击其他地方关闭菜单
function onDocClick() {
  if (ctxMenu.value.show) closeContextMenu()
}

onMounted(() => {
  document.addEventListener('click', onDocClick)
})
onUnmounted(() => {
  document.removeEventListener('click', onDocClick)
})

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

  const batchCommands = demoWidgets.map(w => createCommand(CommandType.ADD_WIDGET, w))
  executeCommand(createCommand(CommandType.BATCH, { commands: batchCommands }))
}
</script>

<style scoped>
.workspace {
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: var(--bg-primary);
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
  box-sizing: border-box;
}

.workspace-toolbar {
  z-index: 10;
  display: flex;
  align-items: center;
  align-self: flex-start;
  gap: 8px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  flex-shrink: 0;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 4px;
}

.toolbar-divider {
  width: 1px;
  height: 20px;
  background: var(--border-color);
  margin: 0 4px;
}

.zoom-btn {
  width: 32px;
  height: 32px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-primary);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
}

.zoom-btn:hover {
  background: var(--bg-tertiary);
  border-color: var(--border-color);
}

.zoom-fit {
  width: auto;
  padding: 0 10px;
}

.board-theme-select {
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
  outline: none;
  transition: all 0.15s;
}

.board-theme-select:hover {
  background: var(--bg-tertiary);
  border-color: var(--border-color);
}

.zoom-label {
  min-width: 48px;
  text-align: center;
  font-size: 13px;
}

.toolbar-btn {
  padding: 6px 12px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-primary);
  font-size: 13px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
}

.toolbar-btn:hover:not(:disabled) {
  background: var(--bg-tertiary);
  border-color: var(--border-color);
}

.toolbar-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

.danger-text {
  color: #ff4560;
}
.danger-text:hover {
  background: rgba(255, 69, 96, 0.12) !important;
}

.btn-layout-fast {
  color: #5de5ff;
}
.btn-layout-fast:hover:not(:disabled) {
  background: rgba(0, 212, 255, 0.15);
}

.btn-layout-ai {
  color: #b794f6;
}
.btn-layout-ai:hover:not(:disabled) {
  background: rgba(123, 97, 255, 0.15);
}

.canvas-shell {
  flex: 1;
  overflow: auto;
  position: relative;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-primary);
}

.canvas {
  position: relative;
  background: var(--bg-secondary, #131837);
  border: 2px solid var(--border-color, #2a3560);
  border-radius: 6px;
  flex-shrink: 0;
  overflow: hidden;
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.3);
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

.empty-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.6; }
.empty-text { font-size: 20px; color: var(--text-secondary); margin-bottom: 8px; }
.empty-sub { font-size: 14px; color: var(--text-muted); margin-bottom: 24px; }

.btn-demo {
  padding: 10px 24px;
  background: linear-gradient(135deg, var(--accent), var(--accent-secondary));
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

/* 右键菜单 */
.context-menu {
  position: fixed;
  z-index: 1000;
  min-width: 140px;
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 8px;
  padding: 4px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.ctx-item {
  width: 100%;
  padding: 8px 12px;
  background: none;
  border: none;
  border-radius: 6px;
  color: var(--text-primary, #e0e6ff);
  font-size: 13px;
  cursor: pointer;
  text-align: left;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.15s;
}

.ctx-item:hover {
  background: rgba(0, 212, 255, 0.08);
}

.ctx-item.danger:hover {
  background: rgba(255, 69, 96, 0.12);
  color: #ff4560;
}
</style>
