<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'
import { useThemeStore } from '../stores/theme'
import { useDialog } from '../composables/useDialog'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const themeStore = useThemeStore()
const { confirm: showConfirm } = useDialog()

const projectId = computed(() => route.params.projectId)
const project = computed(() =>
  projectStore.projects.find(p => p.id === projectId.value) || null
)

// 项目名称编辑
const editingName = ref(false)
const nameInput = ref('')

function startEditName() {
  nameInput.value = project.value?.name || ''
  editingName.value = true
}

function saveName() {
  if (nameInput.value.trim() && project.value) {
    projectStore.updateProjectName(projectId.value, nameInput.value.trim())
  }
  editingName.value = false
}

// 主题列表（从 store 获取，包含内置 + 自定义）
const themes = computed(() =>
  themeStore.allThemes.map(t => ({
    ...t,
    bg: t.vars?.['--bg-primary'] || '#0a0e27',
    accent: t.vars?.['--accent'] || '#00d4ff',
    text: t.vars?.['--text-primary'] || '#e0e6ff',
  }))
)

function changeTheme(themeId) {
  themeStore.applyTheme(themeId)
}

// 自定义主题创建
const showCustomForm = ref(false)
const customName = ref('')
const customBg = ref('#1a1a2e')
const customAccent = ref('#e94560')
const customText = ref('#eaeaea')

function saveCustom() {
  const name = customName.value.trim()
  if (!name) return
  const vars = {
    '--bg-primary': customBg.value,
    '--bg-secondary': adjustBrightness(customBg.value, 10),
    '--bg-tertiary': adjustBrightness(customBg.value, 20),
    '--bg-card': adjustBrightness(customBg.value, 8),
    '--border-color': adjustBrightness(customBg.value, 30),
    '--border-glow': `${customAccent.value}22`,
    '--accent': customAccent.value,
    '--accent-secondary': '#7b61ff',
    '--accent-success': '#00e396',
    '--accent-warning': '#feb019',
    '--accent-danger': '#ff4560',
    '--text-primary': customText.value,
    '--text-secondary': adjustAlpha(customText.value, 0.6),
    '--text-muted': adjustAlpha(customText.value, 0.35),
    '--shadow': '0 4px 24px rgba(0,0,0,0.3)',
    '--shadow-glow': `0 0 20px ${customAccent.value}18`,
    '--font-family': "'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif",
  }
  const id = themeStore.saveCustomTheme(name, vars)
  themeStore.applyTheme(id)
  showCustomForm.value = false
  customName.value = ''
}

async function deleteCustom(themeId) {
  const ok = await showConfirm('确定删除这个自定义主题？')
  if (ok) themeStore.deleteCustomTheme(themeId)
}

// 辅助：调整颜色亮度
function adjustBrightness(hex, amount) {
  const num = parseInt(hex.replace('#', ''), 16)
  const r = Math.min(255, Math.max(0, ((num >> 16) & 0xFF) + amount))
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0xFF) + amount))
  const b = Math.min(255, Math.max(0, (num & 0xFF) + amount))
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`
}

function adjustAlpha(hex, alpha) {
  const num = parseInt(hex.replace('#', ''), 16)
  const r = (num >> 16) & 0xFF
  const g = (num >> 8) & 0xFF
  const b = num & 0xFF
  return `rgba(${r},${g},${b},${alpha})`
}

// 危险操作
async function handleDeleteProject() {
  const ok = await showConfirm(`确定删除项目「${project.value?.name}」？所有看板和数据源都将丢失，此操作不可撤销。`)
  if (!ok) return
  projectStore.deleteProject(projectId.value)
  router.push({ name: 'workspace' })
}
</script>

<template>
  <div class="settings-page">
    <h1 class="page-title">项目设置</h1>

    <!-- 项目名称 -->
    <section class="settings-section">
      <h2>项目名称</h2>
      <div class="name-row" v-if="!editingName">
        <span class="name-value">{{ project?.name || '未命名' }}</span>
        <button class="btn-edit" @click="startEditName">✏️ 编辑</button>
      </div>
      <div class="name-row" v-else>
        <input
          class="name-input"
          v-model="nameInput"
          @keydown.enter="saveName"
          autofocus
        />
        <button class="btn-save" @click="saveName">保存</button>
        <button class="btn-cancel" @click="editingName = false">取消</button>
      </div>
    </section>

    <!-- 系统主题 -->
    <section class="settings-section">
      <h2>系统主题</h2>
      <p class="section-desc">切换整个平台的配色方案</p>
      <div class="theme-grid">
        <div
          v-for="t in themes"
          :key="t.id"
          class="theme-card"
          :class="{ active: themeStore.currentTheme === t.id }"
          @click="changeTheme(t.id)"
        >
          <div class="theme-swatches">
            <span class="swatch" :style="{ background: t.bg }"></span>
            <span class="swatch" :style="{ background: t.accent }"></span>
            <span class="swatch swatch-text" :style="{ background: t.text }"></span>
          </div>
          <div class="theme-label">{{ t.label }}</div>
          <div class="theme-check" v-if="themeStore.currentTheme === t.id">✓</div>
          <button
            v-if="t.isCustom"
            class="theme-delete"
            @click.stop="deleteCustom(t.id)"
            title="删除自定义主题"
          >✕</button>
        </div>
      </div>

      <!-- 创建自定义主题 -->
      <div class="custom-theme-area">
        <button v-if="!showCustomForm" class="btn-create-theme" @click="showCustomForm = true">
          ＋ 创建自定义主题
        </button>
        <div v-else class="custom-form">
          <input v-model="customName" class="name-input" placeholder="主题名称" />
          <div class="color-row">
            <label>背景色 <input type="color" v-model="customBg" /></label>
            <label>强调色 <input type="color" v-model="customAccent" /></label>
            <label>文字色 <input type="color" v-model="customText" /></label>
          </div>
          <div class="custom-preview" :style="{ background: customBg, color: customText, borderColor: customAccent }">
            <span :style="{ color: customAccent }">● 预览效果</span>
            <span>Aa 文字</span>
          </div>
          <div class="custom-actions">
            <button class="btn-save" @click="saveCustom" :disabled="!customName.trim()">保存并应用</button>
            <button class="btn-cancel" @click="showCustomForm = false">取消</button>
          </div>
        </div>
      </div>
    </section>

    <!-- 项目信息 -->
    <section class="settings-section">
      <h2>项目信息</h2>
      <div class="info-grid" v-if="project">
        <div class="info-item">
          <span class="info-label">看板数量</span>
          <span class="info-value">{{ project.dashboards?.length || 0 }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">数据源数量</span>
          <span class="info-value">{{ project.dataSources?.length || 0 }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">创建时间</span>
          <span class="info-value">{{ project.createdAt ? new Date(project.createdAt).toLocaleDateString('zh-CN') : '-' }}</span>
        </div>
      </div>
    </section>

    <!-- 危险区域 -->
    <section class="settings-section danger-zone">
      <h2>⚠️ 危险操作</h2>
      <p class="section-desc">以下操作不可撤销，请谨慎操作</p>
      <button class="btn-danger" @click="handleDeleteProject">🗑 删除此项目</button>
    </section>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 720px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary, #e0e6ff);
  margin: 0 0 32px;
}

.settings-section {
  margin-bottom: 36px;
  padding: 20px 24px;
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 12px;
}

.settings-section h2 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #e0e6ff);
  margin: 0 0 8px;
}

.section-desc {
  font-size: 13px;
  color: var(--text-muted, #4a5578);
  margin: 0 0 16px;
}

/* 名称 */
.name-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
}

.name-value {
  font-size: 18px;
  font-weight: 500;
  color: var(--text-primary, #e0e6ff);
}

.name-input {
  flex: 1;
  padding: 8px 12px;
  background: var(--bg-tertiary, #1a2045);
  border: 1px solid var(--accent, #00d4ff);
  border-radius: 8px;
  color: var(--text-primary, #e0e6ff);
  font-size: 16px;
  outline: none;
}

.btn-edit, .btn-save, .btn-cancel {
  padding: 6px 14px;
  border-radius: 8px;
  border: 1px solid var(--border-color, #2a3560);
  background: var(--bg-tertiary, #1a2045);
  color: var(--text-secondary, #8892b0);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-edit:hover, .btn-cancel:hover {
  border-color: var(--accent, #00d4ff);
  color: var(--text-primary, #e0e6ff);
}

.btn-save {
  background: var(--accent, #00d4ff);
  color: #fff;
  border-color: var(--accent, #00d4ff);
}

/* 主题卡片 */
.theme-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.theme-card {
  padding: 14px;
  background: var(--bg-tertiary, #1a2045);
  border: 2px solid var(--border-color, #2a3560);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  text-align: center;
}

.theme-card:hover {
  border-color: var(--accent, #00d4ff);
  transform: translateY(-1px);
}

.theme-card.active {
  border-color: var(--accent, #00d4ff);
  box-shadow: 0 0 12px rgba(0, 212, 255, 0.15);
}

.theme-swatches {
  display: flex;
  gap: 6px;
  justify-content: center;
  margin-bottom: 10px;
}

.swatch {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.1);
}

.swatch-text {
  width: 18px;
  height: 18px;
}

.theme-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary, #e0e6ff);
}

.theme-check {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 12px;
  color: var(--accent, #00d4ff);
  font-weight: 700;
}

.theme-delete {
  position: absolute;
  top: 6px;
  left: 6px;
  width: 18px;
  height: 18px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 69, 96, 0.2);
  color: #ff4560;
  font-size: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.15s;
}

.theme-card:hover .theme-delete {
  opacity: 1;
}

.custom-theme-area {
  margin-top: 16px;
}

.btn-create-theme {
  width: 100%;
  padding: 10px;
  border: 2px dashed var(--border-color, #2a3560);
  border-radius: 10px;
  background: transparent;
  color: var(--text-muted, #4a5578);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-create-theme:hover {
  border-color: var(--accent, #00d4ff);
  color: var(--accent, #00d4ff);
}

.custom-form {
  background: var(--bg-tertiary, #1a2045);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.color-row {
  display: flex;
  gap: 16px;
}

.color-row label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary, #8892b0);
}

.color-row input[type="color"] {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  background: transparent;
}

.custom-preview {
  padding: 12px 16px;
  border-radius: 8px;
  border: 2px solid;
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.custom-actions {
  display: flex;
  gap: 8px;
}

/* 信息网格 */
.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 12px;
}

.info-item {
  text-align: center;
  padding: 12px;
  background: var(--bg-tertiary, #1a2045);
  border-radius: 8px;
}

.info-label {
  display: block;
  font-size: 12px;
  color: var(--text-muted, #4a5578);
  margin-bottom: 4px;
}

.info-value {
  display: block;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary, #e0e6ff);
}

/* 危险区域 */
.danger-zone {
  border-color: rgba(255, 69, 96, 0.3);
}

.danger-zone h2 {
  color: #ff4560;
}

.btn-danger {
  padding: 8px 20px;
  border-radius: 8px;
  border: 1px solid rgba(255, 69, 96, 0.4);
  background: rgba(255, 69, 96, 0.08);
  color: #ff4560;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-danger:hover {
  background: rgba(255, 69, 96, 0.15);
  border-color: #ff4560;
}
</style>
