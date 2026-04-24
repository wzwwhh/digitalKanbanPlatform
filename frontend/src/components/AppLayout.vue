<template>
  <div class="app-layout">
    <!-- 顶栏 -->
    <header class="top-bar">
      <div class="top-left">
        <button class="btn-icon" @click="goHome" title="返回首页">🏠</button>
        <span class="project-name">{{ projectStore.currentProject?.name }}</span>
      </div>
      <div class="top-center">
        <!-- 主题切换预留 -->
      </div>
      <div class="top-right">
        <span v-if="saveMsg" class="save-toast">{{ saveMsg }}</span>
        <button class="btn-icon" @click="handleUndo" :disabled="!historyStore.canUndo" title="撤销">↩</button>
        <button class="btn-icon" @click="handleRedo" :disabled="!historyStore.canRedo" title="重做">↪</button>
        <button class="btn" @click="handleSave">💾 保存</button>
        <button class="btn btn-primary" @click="handleExport">📦 导出</button>
      </div>
    </header>

    <!-- 主体 -->
    <div class="main-area">
      <!-- 左侧素材库 -->
      <aside class="sidebar-left">
        <div class="sidebar-header">素材库</div>
        <div class="material-list">
          <div
            v-for="(config, type) in widgetRegistry"
            :key="type"
            class="material-item"
            @click="addWidgetFromLib(type, config)"
          >
            <span class="mat-icon">{{ config.icon }}</span>
            <span class="mat-label">{{ config.label }}</span>
          </div>
        </div>
      </aside>

      <!-- 中间画布 -->
      <main class="workspace-area">
        <Workspace />
      </main>

      <!-- 右侧面板 -->
      <aside class="sidebar-right">
        <div class="panel-tabs">
          <button
            class="tab"
            :class="{ active: rightTab === 'props' }"
            @click="rightTab = 'props'"
          >属性</button>
          <button
            class="tab"
            :class="{ active: rightTab === 'ai' }"
            @click="rightTab = 'ai'"
          >AI 助手</button>
        </div>
        <div class="panel-content">
          <PropEditor v-if="rightTab === 'props'" />
          <AiChat v-else />
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useProjectStore } from '../stores/project'
import { useDashboardStore } from '../stores/dashboard'
import { useHistoryStore } from '../stores/history'
import { undo, redo, executeCommand, createCommand, CommandType } from '../core/command'
import { getAllWidgets } from '../core/registry'
import Workspace from './Workspace.vue'
import PropEditor from './PropEditor.vue'
import AiChat from './AiChat.vue'

const projectStore = useProjectStore()
const dashboardStore = useDashboardStore()
const historyStore = useHistoryStore()

const rightTab = ref('ai')
const widgetRegistry = computed(() => getAllWidgets())

// 选中组件时自动切到属性 tab
watch(() => dashboardStore.selectedId, (id) => {
  if (id) rightTab.value = 'props'
})

function goHome() {
  if (confirm('返回首页？未保存的修改会丢失。')) {
    projectStore.closeProject()
    dashboardStore.clearAll()
    historyStore.clear()
  }
}

function handleUndo() { undo() }
function handleRedo() { redo() }

const saveMsg = ref('')
function handleSave() {
  projectStore.saveProject(dashboardStore.widgets)
  saveMsg.value = '✅ 已保存'
  setTimeout(() => saveMsg.value = '', 2000)
}

function handleExport() {
  alert('导出功能开发中（模块 J）')
}

function addWidgetFromLib(type, config) {
  const widget = {
    type,
    props: {},
    position: { x: 100 + Math.random() * 200, y: 100 + Math.random() * 200 },
    size: { ...config.defaultSize },
  }
  // 填充 schema 默认值
  if (config.schema) {
    Object.entries(config.schema).forEach(([key, field]) => {
      widget.props[key] = field.default
    })
  }
  executeCommand(createCommand(CommandType.ADD_WIDGET, widget))
}
</script>

<style scoped>
.app-layout {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

/* 顶栏 */
.top-bar {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.top-left, .top-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.project-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.btn-icon {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 16px;
  cursor: pointer;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.btn-icon:hover:not(:disabled) {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-icon:disabled {
  opacity: 0.3;
  cursor: default;
}

.btn {
  padding: 6px 14px;
  border: 1px solid var(--border-color);
  background: var(--bg-tertiary);
  color: var(--text-primary);
  font-size: 13px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn:hover {
  border-color: var(--accent);
}

.btn-primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.btn-primary:hover {
  opacity: 0.9;
}

/* 主体 */
.main-area {
  flex: 1;
  display: flex;
  min-height: 0;
}

/* 侧栏 */
.sidebar-left, .sidebar-right {
  width: 220px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

.sidebar-right {
  border-right: none;
  border-left: 1px solid var(--border-color);
  width: 280px;
}

.sidebar-header {
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
}

.sidebar-placeholder, .panel-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 14px;
}

.hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

/* 右侧 Tab */
.panel-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-color);
}

.tab {
  flex: 1;
  padding: 10px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  border-bottom: 2px solid transparent;
}

.tab.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

.tab:hover:not(.active) {
  color: var(--text-primary);
}

.panel-content {
  flex: 1;
  overflow-y: auto;
}

/* 画布区域 */
.workspace-area {
  flex: 1;
  overflow: hidden;
  position: relative;
}

/* 保存提示 */
.save-toast {
  font-size: 12px;
  color: var(--accent-success);
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 素材库列表 */
.material-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.material-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.12s;
  font-size: 13px;
  color: var(--text-secondary);
}

.material-item:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.mat-icon {
  font-size: 16px;
  width: 24px;
  text-align: center;
  flex-shrink: 0;
}

.mat-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
