<template>
  <div class="app-layout">
    <!-- 顶栏 -->
    <header class="top-bar">
      <div class="top-left">
        <button class="btn-icon" @click="goBack" title="返回看板列表">←</button>
        <span class="project-name">{{ dashboardName || projectStore.currentProject?.name }}</span>
        <div class="divider"></div>
        <button class="btn-icon" @click="handleUndo" :disabled="!historyStore.canUndo" title="撤销 (Ctrl+Z)">↩</button>
        <button class="btn-icon" @click="handleRedo" :disabled="!historyStore.canRedo" title="重做 (Ctrl+Y)">↪</button>
        <span v-if="saveMsg" class="save-indicator">{{ saveMsg }}</span>
      </div>
      <div class="top-center">
        <!-- 中间留空或显示状态 -->
      </div>
      <div class="top-right">
        <button class="btn btn-ghost" @click="handlePreview" title="预览看板">👁 预览</button>
        <button class="btn btn-ghost" @click="handleSave" title="保存 (Ctrl+S)">💾 保存</button>
        <button class="btn btn-primary" @click="handleExport">📦 导出</button>
        <div class="divider"></div>
        <ThemePicker
          :currentSystemTheme="themeStore.currentTheme"
          :showBoardStyle="false"
          @change-system="themeStore.applyTheme($event)"
        />
        <button class="btn-icon" @click="showShortcuts = true" title="快捷键帮助 (?)">?</button>
      </div>
    </header>

    <!-- 主体 -->
    <div class="main-area">
      <!-- 左侧素材库 -->
      <aside class="sidebar-left">
        <div class="sidebar-header">素材库</div>
        <input
          class="mat-search"
          type="text"
          v-model="matSearch"
          placeholder="搜索组件..."
        />
        <div class="material-list">
          <template v-for="(items, cat) in groupedWidgets" :key="cat">
            <div class="mat-category" @click="toggleCategory(cat)">
              <span>{{ cat }}</span>
              <span class="cat-arrow">{{ collapsedCats.has(cat) ? '▸' : '▾' }}</span>
            </div>
            <template v-if="!collapsedCats.has(cat)">
              <div
                v-for="item in items"
                :key="item.type"
                class="material-item"
                @click="addWidgetFromLib(item.type, item.config)"
              >
                <span class="mat-icon">{{ item.config.icon }}</span>
                <span class="mat-label">{{ item.config.label }}</span>
              </div>
            </template>
          </template>
        </div>

        <!-- 自定义模板 -->
        <template v-if="customTemplatesStore.templates.length > 0">
          <div class="mat-category custom-cat">
            <span>⭐ 我的模板</span>
          </div>
          <div
            v-for="tpl in customTemplatesStore.templates"
            :key="tpl.id"
            class="material-item custom-tpl"
            @click="addFromTemplate(tpl)"
          >
            <span class="mat-icon">{{ tpl.icon }}</span>
            <span class="mat-label">{{ tpl.name }}</span>
          </div>
        </template>
      </aside>

      <!-- 中间画布 -->
      <main class="workspace-area" :style="boardThemeVars">
        <Workspace 
          v-model:boardTheme="boardTheme" 
          v-model:bgImage="bgImage"
          :layoutLoading="layoutLoading"
          @open-ds="showDsDrawer = true"
          @auto-layout="handleAutoLayout"
        />
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
          <PropEditor v-show="rightTab === 'props'" />
          <AiChat v-show="rightTab === 'ai'" :initialPrompt="props.aiPrompt" />
        </div>
      </aside>
    </div>

    <!-- 状态栏 -->
    <div class="status-bar">
      <span>📦 组件: {{ dashboardStore.widgets.length }}</span>
      <span>🔗 数据源: {{ dsCount }}</span>
      <span v-if="lastSaved">💾 {{ lastSaved }}</span>
      <span v-if="boardTheme" class="board-theme-indicator">🎨 {{ boardTheme }}</span>
    </div>

    <!-- 数据源抽屉组件 -->
    <DataSourceDrawer v-model:visible="showDsDrawer" />

    <!-- 全局 Toast -->
    <Transition name="toast">
      <div v-if="toastMsg" class="float-toast" :class="toastType">{{ toastMsg }}</div>
    </Transition>

    <!-- 快捷键帮助 -->
    <ShortcutsHelp :visible="showShortcuts" @close="showShortcuts = false" />

    <!-- 导出弹窗 -->
    <Transition name="fade">
      <div class="modal-overlay" v-if="showExportModal">
        <div class="export-modal">
          <div class="modal-header">
            <h3>📦 选择导出模式</h3>
            <button class="btn-icon close-btn" @click="showExportModal = false">×</button>
          </div>
          <div class="modal-body">
            <div class="export-option" @click="confirmExport('zip')">
              <div class="export-icon">🗂️</div>
              <div class="export-desc">
                <h4>ZIP 部署包</h4>
                <p>含 server.py + README + 数据源，适合服务器部署</p>
              </div>
            </div>
            <div class="export-option" @click="confirmExport('html')">
              <div class="export-icon">📄</div>
              <div class="export-desc">
                <h4>单个 HTML 文件</h4>
                <p>纯前端静态文件，适合快速预览和轻量分享</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'
import { useDashboardStore } from '../stores/dashboard'
import { useHistoryStore } from '../stores/history'
import { useThemeStore } from '../stores/theme'
import { undo, redo, executeCommand, createCommand, CommandType } from '../core/command'
import { getAllWidgets } from '../core/registry'
import Workspace from './Workspace.vue'
import PropEditor from './PropEditor.vue'
import AiChat from './AiChat.vue'
import ThemePicker from './ThemePicker.vue'
import ShortcutsHelp from './ShortcutsHelp.vue'
import DataSourceDrawer from './DataSourceDrawer.vue'
import { useCustomTemplatesStore } from '../stores/customTemplates'

const props = defineProps({
  projectId: { type: String, default: '' },
  dashboardId: { type: String, default: '' },
  aiPrompt: { type: String, default: '' },
})

const router = useRouter()
const projectStore = useProjectStore()
const dashboardStore = useDashboardStore()
const historyStore = useHistoryStore()
const themeStore = useThemeStore()
const customTemplatesStore = useCustomTemplatesStore()

const rightTab = ref('ai')
const matSearch = ref('')
const showDsDrawer = ref(false)
const showShortcuts = ref(false)
const showExportModal = ref(false)
const collapsedCats = ref(new Set())
const boardTheme = ref(null)  // 画布独立主题，null = 跟随系统
const bgImage = ref(null)     // 大屏背景图
const layoutLoading = ref('')  // '' | 'fast' | 'ai'

// 画布独立主题 CSS 变量
const boardThemeVars = computed(() => {
  if (!boardTheme.value) return {}
  const t = themeStore.allThemes.find(th => th.id === boardTheme.value)
  return t?.vars || {}
})

const widgetRegistry = computed(() => getAllWidgets())

// 按分类分组 + 搜索过滤
const groupedWidgets = computed(() => {
  const all = getAllWidgets()
  const groups = {}
  for (const [type, config] of Object.entries(all)) {
    // 搜索过滤
    if (matSearch.value) {
      const q = matSearch.value.toLowerCase()
      if (!config.label.toLowerCase().includes(q) && !type.toLowerCase().includes(q)) continue
    }
    const cat = config.category || '其他'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push({ type, config })
  }
  return groups
})

function toggleCategory(cat) {
  const s = new Set(collapsedCats.value)
  if (s.has(cat)) s.delete(cat)
  else s.add(cat)
  collapsedCats.value = s
}

// 数据源计数
const dsCount = computed(() => (projectStore.currentProject?.dataSources || []).length)

const lastSaved = computed(() => {
  if (!props.projectId || !props.dashboardId) return ''
  const db = projectStore.getDashboard(props.projectId, props.dashboardId)
  if (!db?.savedAt) return ''
  const d = new Date(db.savedAt)
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
})

// 看板名称
const dashboardName = computed(() => {
  if (props.projectId && props.dashboardId) {
    const db = projectStore.getDashboard(props.projectId, props.dashboardId)
    return db?.name || ''
  }
  return projectStore.currentProject?.name || ''
})

// 选中组件时自动切到属性 tab
watch(() => dashboardStore.selectedId, (id) => {
  if (id) rightTab.value = 'props'
})

// 自动保存 (防抖)
let autoSaveTimer = null
watch(() => dashboardStore.widgets, () => {
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
  autoSaveTimer = setTimeout(() => {
    if (props.projectId && props.dashboardId) {
      projectStore.saveDashboard(props.projectId, props.dashboardId, dashboardStore.widgets, boardTheme.value, bgImage.value)
    } else {
      projectStore.saveProject(dashboardStore.widgets)
    }
  }, 1000)
}, { deep: true })

// 键盘事件：Delete/Backspace 删除选中组件
function onKeyDown(e) {
  // 如果焦点在输入框内则忽略
  const tag = e.target.tagName.toLowerCase()
  if (tag === 'input' || tag === 'textarea' || tag === 'select') return

  if ((e.key === 'Delete' || e.key === 'Backspace') && dashboardStore.selectedId) {
    e.preventDefault()
    executeCommand(createCommand(CommandType.DELETE_WIDGET, { id: dashboardStore.selectedId }))
  }
  // Ctrl+Z 撤销, Ctrl+Shift+Z / Ctrl+Y 重做
  if (e.ctrlKey && e.key === 'z' && !e.shiftKey) { e.preventDefault(); undo() }
  if (e.ctrlKey && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) { e.preventDefault(); redo() }
  // Ctrl+S 保存
  if (e.ctrlKey && e.key === 's') { e.preventDefault(); handleSave() }
  // Ctrl+D 复制选中组件
  if (e.ctrlKey && e.key === 'd' && dashboardStore.selectedId) {
    e.preventDefault()
    const w = dashboardStore.widgets.find(i => i.id === dashboardStore.selectedId)
    if (w) {
      executeCommand(createCommand(CommandType.ADD_WIDGET, {
        type: w.type,
        props: JSON.parse(JSON.stringify(w.props)),
        position: { x: w.position.x + 30, y: w.position.y + 30 },
        size: { ...w.size },
        dataSource: w.dataSource ? JSON.parse(JSON.stringify(w.dataSource)) : undefined,
      }))
    }
  }
  // ? 快捷键帮助
  if (e.key === '?' && !e.ctrlKey) {
    showShortcuts.value = !showShortcuts.value
  }
}

// 加载看板数据
onMounted(() => {
  // 确保项目已加载
  if (props.projectId) {
    projectStore.loadProject(props.projectId)
  }

  // 加载看板 widgets
  if (props.projectId && props.dashboardId) {
    const db = projectStore.getDashboard(props.projectId, props.dashboardId)
    if (db && db.widgets) {
      dashboardStore.setWidgets(db.widgets)
    } else {
      dashboardStore.clearAll()
    }
  } else if (projectStore.currentProject?.widgets?.length) {
    // 兼容旧版：项目级 widgets
    dashboardStore.setWidgets(projectStore.currentProject.widgets)
  }

  // 加载看板独立主题和背景
  if (props.projectId && props.dashboardId) {
    const db = projectStore.getDashboard(props.projectId, props.dashboardId)
    if (db?.boardTheme) {
      boardTheme.value = db.boardTheme
    }
    if (db?.bgImage) {
      bgImage.value = db.bgImage
    }
  }

  // 初始化主题
  themeStore.initTheme()
  // 清空历史
  historyStore.clear()
  // 注册键盘事件
  document.addEventListener('keydown', onKeyDown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', onKeyDown)
})

function goBack() {
  if (props.projectId) {
    router.push({ name: 'dashboards', params: { projectId: props.projectId } })
  } else {
    router.push('/')
  }
}

function handlePreview() {
  if (props.projectId && props.dashboardId) {
    // 先保存再预览
    projectStore.saveDashboard(props.projectId, props.dashboardId, dashboardStore.widgets)
    router.push({
      name: 'dashboard-preview',
      params: { projectId: props.projectId, dashboardId: props.dashboardId },
    })
  }
}

function goToDataSources() {
  showDsDrawer.value = false
  if (props.projectId) {
    router.push({ name: 'datasources', params: { projectId: props.projectId } })
  }
}

function handleUndo() { undo() }
function handleRedo() { redo() }

const saveMsg = ref('')
const toastMsg = ref('')
const toastType = ref('success')
let toastTimer = null

function showToast(msg, type = 'success', duration = 2000) {
  if (toastTimer) clearTimeout(toastTimer)
  toastMsg.value = msg
  toastType.value = type
  toastTimer = setTimeout(() => { toastMsg.value = '' }, duration)
}

function handleSave() {
  if (props.projectId && props.dashboardId) {
    projectStore.saveDashboard(props.projectId, props.dashboardId, dashboardStore.widgets, boardTheme.value, bgImage.value)
  } else {
    projectStore.saveProject(dashboardStore.widgets)
  }
  saveMsg.value = '✅ 已保存'
  setTimeout(() => saveMsg.value = '', 2000)
  showToast('✅ 保存成功')
}

function handleExport() {
  if (!projectStore.currentProject) return
  showExportModal.value = true
}

async function confirmExport(type) {
  showExportModal.value = false
  const useZip = type === 'zip'

  const payload = {
    projectName: dashboardName.value || projectStore.currentProject.name,
    widgets: dashboardStore.widgets,
    dataSources: projectStore.currentProject?.dataSources || [],
    theme: boardTheme.value || themeStore.currentTheme,
    canvasWidth: 1920,
    canvasHeight: 1080,
  }

  try {
    if (useZip) {
      const response = await fetch('/api/export/zip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await response.json()
      // base64 → blob → download
      const byteChars = atob(data.zipBase64)
      const byteArray = new Uint8Array(byteChars.length)
      for (let i = 0; i < byteChars.length; i++) byteArray[i] = byteChars.charCodeAt(i)
      const blob = new Blob([byteArray], { type: 'application/zip' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = data.filename || 'dashboard.zip'
      a.click()
      URL.revokeObjectURL(url)
      showToast('📦 ZIP 部署包导出成功')
    } else {
      const response = await fetch('/api/export/html', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await response.json()
      const blob = new Blob([data.html], { type: 'text/html;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = data.filename || `${dashboardName.value || 'dashboard'}.html`
      a.click()
      URL.revokeObjectURL(url)
      showToast('📦 HTML 导出成功')
    }
  } catch (err) {
    showToast(`导出失败: ${err.message}`, 'error', 4000)
  }
}

function addWidgetFromLib(type, config) {
  const widget = {
    type,
    props: {},
    position: { x: 100 + Math.random() * 200, y: 100 + Math.random() * 200 },
    size: { ...config.defaultSize },
  }
  if (config.schema) {
    Object.entries(config.schema).forEach(([key, field]) => {
      widget.props[key] = field.default
    })
  }
  executeCommand(createCommand(CommandType.ADD_WIDGET, widget))
}

// 从自定义模板添加组件
function addFromTemplate(tpl) {
  const all = getAllWidgets()
  const config = all[tpl.baseType]
  if (!config) return

  const widget = {
    type: tpl.baseType,
    props: { ...(tpl.presetProps || {}) },
    position: { x: 100 + Math.random() * 200, y: 100 + Math.random() * 200 },
    size: { ...(config.defaultSize || { w: 300, h: 200 }) },
  }
  // 填充 schema 中缺失的默认值
  if (config.schema) {
    Object.entries(config.schema).forEach(([key, field]) => {
      if (widget.props[key] === undefined) {
        widget.props[key] = field.default
      }
    })
  }
  executeCommand(createCommand(CommandType.ADD_WIDGET, widget))
}

// ===== 排版 =====
async function handleAutoLayout(mode = 'ai') {
  if (layoutLoading.value || dashboardStore.widgets.length === 0) return

  layoutLoading.value = mode
  try {
    // AI 模式传语义丰富 context，快速模式传精简 context
    const widgetsList = mode === 'ai'
      ? dashboardStore.widgets.map(w => ({
          id: w.id,
          type: w.type,
          title: w.props?.title || '',
          hasData: !!(w.dataSource?.sourceId),
          dataFields: w.dataSource?.mapping || null,
          position: w.position,
          size: w.size,
        }))
      : dashboardStore.widgets.map(w => ({
          id: w.id,
          type: w.type,
          props: { title: w.props?.title },
          position: w.position,
          size: w.size,
        }))

    const context = {
      widgets: widgetsList,
      dataSources: mode === 'ai'
        ? (projectStore.currentProject?.dataSources || []).map(ds => ({
            id: ds.id, name: ds.name, fields: (ds.fields || []).slice(0, 8),
          }))
        : [],
      selectedId: null,
      layout_mode: mode,
    }

    const controller = new AbortController()
    const timeoutMs = mode === 'fast' ? 10000 : 300000
    const timeout = setTimeout(() => controller.abort(new Error("AI 排版超时，请重试或使用快速排版")), timeoutMs)
    const response = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: '排版', context }),
      signal: controller.signal,
    })
    clearTimeout(timeout)

    if (!response.ok) throw new Error(`服务器错误: ${response.status}`)

    const data = await response.json()

    if (data.commands?.length > 0) {
      for (const cmd of data.commands) {
        applyLayoutCommand(cmd)
      }
      showToast(mode === 'fast' ? '⚡ 快速排版完成' : '✨ AI排版完成')
    } else {
      showToast(data.message || '排版未产生变更', 'error', 3000)
    }
  } catch (err) {
    showToast(`排版失败: ${err.message}`, 'error', 4000)
  } finally {
    layoutLoading.value = ''
  }
}

/** 执行排版返回的命令（只允许 MOVE/RESIZE/BATCH） */
function applyLayoutCommand(cmd) {
  if (!cmd || !cmd.type) return
  switch (cmd.type) {
    case 'MOVE_WIDGET':
      executeCommand(createCommand(CommandType.MOVE_WIDGET, cmd.payload, 'ai'))
      break
    case 'RESIZE_WIDGET':
      executeCommand(createCommand(CommandType.RESIZE_WIDGET, cmd.payload, 'ai'))
      break
    case 'BATCH':
      if (cmd.payload?.commands) {
        cmd.payload.commands.forEach(sub => applyLayoutCommand(sub))
      }
      break
    // 其他类型（ADD/DELETE等）静默忽略，确保安全
  }
}
</script>

<style scoped>
.app-layout {
  width: 100%;
  height: 100vh;
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

.top-left, .top-right, .menu-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.divider {
  width: 1px;
  height: 20px;
  background: var(--border-color);
  margin: 0 4px;
}

.save-indicator {
  font-size: 12px;
  color: var(--accent-success, #00e676);
  margin-left: 8px;
  animation: fadeIn 0.2s ease;
}

.board-theme-select {
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid var(--border-color, #2a2d45);
  background: var(--bg-primary, #0a0e1a);
  color: var(--text-primary, #e0e6ff);
  font-size: 12px;
  cursor: pointer;
  outline: none;
}

.project-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.widget-count {
  font-size: 12px;
  color: var(--text-muted);
  padding: 3px 10px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
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

.btn-ghost {
  background: transparent;
  border-color: transparent;
}

.btn-ghost:hover {
  background: var(--bg-secondary);
  border-color: transparent;
  color: var(--accent);
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

/* Search */
.mat-search {
  display: block;
  width: calc(100% - 16px);
  margin: 4px 8px 8px;
  padding: 6px 10px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 12px;
  outline: none;
  box-sizing: border-box;
}

.mat-search:focus {
  border-color: var(--accent);
}

/* Category headers */
.mat-category {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  user-select: none;
}

.mat-category:hover {
  color: var(--text-secondary);
}

.cat-arrow {
  font-size: 10px;
}

/* DS count in toolbar */
.ds-count {
  font-size: 12px;
  color: var(--text-muted);
  margin-left: 4px;
}

/* Data Source Drawer */
.ds-drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 200;
  display: flex;
  justify-content: flex-end;
}

.ds-drawer {
  width: 360px;
  background: var(--bg-secondary);
  border-left: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.drawer-section-title {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.drawer-ds-card {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
}

.drawer-ds-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.drawer-ds-url {
  font-size: 11px;
  color: var(--text-muted);
  font-family: monospace;
  margin-bottom: 8px;
}

.drawer-ds-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.drawer-field {
  font-size: 11px;
  padding: 2px 6px;
  background: rgba(0, 212, 255, 0.08);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 3px;
  color: var(--accent);
}

.drawer-field-more {
  font-size: 11px;
  padding: 2px 6px;
  color: var(--text-muted);
}

.drawer-empty {
  text-align: center;
  padding: 40px 0;
  color: var(--text-muted);
  font-size: 14px;
}

.drawer-add-btn {
  display: block;
  width: 100%;
  margin-top: 16px;
  padding: 10px;
  background: transparent;
  border: 1px dashed var(--border-color);
  border-radius: 8px;
  color: var(--accent);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.drawer-add-btn:hover {
  background: rgba(0, 212, 255, 0.05);
  border-color: var(--accent);
}

/* Drawer transitions */
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.2s ease;
}

.drawer-enter-active .ds-drawer,
.drawer-leave-active .ds-drawer {
  transition: transform 0.25s ease;
}

.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}

.drawer-enter-from .ds-drawer,
.drawer-leave-to .ds-drawer {
  transform: translateX(100%);
}

/* Floating Toast */
.float-toast {
  position: fixed;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  z-index: 9999;
  pointer-events: none;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.float-toast.success {
  background: linear-gradient(135deg, rgba(0, 227, 150, 0.15), rgba(0, 212, 255, 0.15));
  border: 1px solid rgba(0, 227, 150, 0.3);
  color: #00e396;
}

.float-toast.error {
  background: linear-gradient(135deg, rgba(255, 69, 96, 0.15), rgba(255, 130, 50, 0.15));
  border: 1px solid rgba(255, 69, 96, 0.3);
  color: #ff4560;
}

/* Toast transitions */
.toast-enter-active { transition: all 0.3s ease; }
.toast-leave-active { transition: all 0.2s ease; }
.toast-enter-from { opacity: 0; transform: translateX(-50%) translateY(20px); }
.toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(10px); }

/* Save indicator in topbar */
.save-indicator {
  font-size: 12px;
  color: #00e396;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 状态栏 */
.status-bar {
  height: 26px;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 16px;
  background: var(--bg-secondary, #131837);
  border-top: 1px solid var(--border-color, #2a2d45);
  font-size: 11px;
  color: var(--text-muted, #4a5578);
  flex-shrink: 0;
}

.board-theme-indicator {
  margin-left: auto;
  color: var(--accent, #00d4ff);
}

/* 自定义模板分类 */
.custom-cat {
  border-top: 1px solid var(--border-color, #2a2d45);
  margin-top: 8px;
  padding-top: 8px;
  color: #fbbf24 !important;
}

.custom-tpl {
  background: rgba(251, 191, 36, 0.05);
}

/* 导出弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(2px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.export-modal {
  background: var(--bg-secondary, #1a1d2d);
  border: 1px solid var(--border-color, #2a2d45);
  border-radius: 12px;
  width: 440px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color, #2a2d45);
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  color: var(--text-primary, #e0e6ff);
  font-weight: 600;
}

.close-btn {
  font-size: 20px;
  width: 28px;
  height: 28px;
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.export-option {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--bg-tertiary, #21263f);
  border: 1px solid var(--border-color, #2a2d45);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.export-option:hover {
  border-color: var(--accent, #00d4ff);
  background: rgba(0, 212, 255, 0.05);
  transform: translateY(-2px);
}

.export-icon {
  font-size: 32px;
}

.export-desc h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: var(--text-primary, #e0e6ff);
}

.export-desc p {
  margin: 0;
  font-size: 12px;
  color: var(--text-muted, #8a94b5);
  line-height: 1.4;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

