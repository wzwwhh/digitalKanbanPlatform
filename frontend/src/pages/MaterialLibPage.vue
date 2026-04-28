<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getAllWidgets } from '../core/registry'
import { useCustomTemplatesStore } from '../stores/customTemplates'
import { useDialog } from '../composables/useDialog'

const router = useRouter()
const route = useRoute()
const templateStore = useCustomTemplatesStore()
const { confirm: showConfirm } = useDialog()

const projectId = computed(() => route.params.projectId)

// 内置组件列表
const builtinWidgets = computed(() => {
  const all = getAllWidgets()
  return Object.entries(all).map(([type, config]) => ({
    type,
    label: config.label,
    icon: config.icon,
    category: config.category,
    schema: config.schema || {},
    defaultSize: config.defaultSize || { w: 300, h: 200 },
  }))
})

// 按分类分组
const grouped = computed(() => {
  const groups = {}
  for (const w of builtinWidgets.value) {
    if (!groups[w.category]) groups[w.category] = []
    groups[w.category].push(w)
  }
  return groups
})

// ========== 新建模板 ==========
const showCreateDialog = ref(false)
const newTemplate = ref({
  name: '',
  baseType: 'kpi',
  icon: '⭐',
  description: '',
  presetProps: {},
})

// 当前选中的基础组件的 schema
const currentSchema = computed(() => {
  const all = getAllWidgets()
  return all[newTemplate.value.baseType]?.schema || {}
})

function openCreateDialog() {
  newTemplate.value = { name: '', baseType: 'kpi', icon: '⭐', description: '', presetProps: {} }
  showCreateDialog.value = true
}

function onBaseTypeChange() {
  // 重新初始化 presetProps
  const schema = currentSchema.value
  const props = {}
  for (const [key, field] of Object.entries(schema)) {
    props[key] = field.default
  }
  newTemplate.value.presetProps = props
}

function saveTemplate() {
  if (!newTemplate.value.name.trim()) return
  templateStore.addTemplate({
    name: newTemplate.value.name,
    baseType: newTemplate.value.baseType,
    icon: newTemplate.value.icon,
    description: newTemplate.value.description,
    presetProps: { ...newTemplate.value.presetProps },
  })
  showCreateDialog.value = false
}

async function removeTemplate(id) {
  const ok = await showConfirm('确定删除此模板？')
  if (ok) templateStore.deleteTemplate(id)
}

// ========== AI 添加 ==========
const aiInput = ref('')
const aiLoading = ref(false)

async function aiCreateTemplate() {
  if (!aiInput.value.trim() || aiLoading.value) return
  aiLoading.value = true

  try {
    const resp = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: `请根据以下描述创建一个组件模板（返回JSON包含type/title/color等属性）：${aiInput.value}`,
        context: { widgets: [], selectedId: null, dataSources: [] },
      }),
    })
    const data = await resp.json()

    // 尝试从 AI 命令中提取模板
    if (data.commands?.length > 0) {
      const cmd = data.commands[0]
      const props = cmd.payload || {}
      templateStore.addTemplate({
        name: aiInput.value.slice(0, 20),
        baseType: props.type || 'kpi',
        icon: '🤖',
        description: `AI 生成: ${aiInput.value}`,
        presetProps: props.props || props,
      })
      aiInput.value = ''
    }
  } catch (e) {
    console.error('AI 创建模板失败', e)
  } finally {
    aiLoading.value = false
  }
}

function goToEditor() {
  if (projectId.value) {
    router.push({ name: 'dashboards', params: { projectId: projectId.value } })
  }
}
</script>

<template>
  <div class="material-lib-page">
    <div class="page-header">
      <h1>🧩 素材库管理</h1>
      <button class="btn-create" @click="openCreateDialog">＋ 新建模板</button>
    </div>

    <!-- AI 快速创建 -->
    <section class="ai-create-section">
      <div class="ai-create-row">
        <input
          v-model="aiInput"
          class="ai-input"
          placeholder="描述你想要的组件模板，如「红色销售KPI卡，标题今日销售额」"
          @keydown.enter="aiCreateTemplate"
        />
        <button class="btn-ai" @click="aiCreateTemplate" :disabled="aiLoading || !aiInput.trim()">
          {{ aiLoading ? '生成中...' : '🤖 AI 生成' }}
        </button>
      </div>
    </section>

    <!-- 自定义模板 -->
    <section class="templates-section" v-if="templateStore.templates.length > 0">
      <div class="section-title">📌 我的自定义模板（{{ templateStore.templates.length }}）</div>
      <div class="template-grid">
        <div v-for="tpl in templateStore.templates" :key="tpl.id" class="template-card">
          <div class="tpl-header">
            <span class="tpl-icon">{{ tpl.icon }}</span>
            <span class="tpl-name">{{ tpl.name }}</span>
          </div>
          <div class="tpl-type">基础类型: {{ tpl.baseType }}</div>
          <div class="tpl-desc" v-if="tpl.description">{{ tpl.description }}</div>
          <div class="tpl-actions">
            <button class="btn-sm danger" @click="removeTemplate(tpl.id)">删除</button>
          </div>
        </div>
      </div>
    </section>

    <!-- 内置组件 -->
    <section class="builtin-section">
      <div class="section-title">📦 内置组件（{{ builtinWidgets.length }} 个）</div>
      <template v-for="(items, cat) in grouped" :key="cat">
        <div class="category-title">{{ cat }}</div>
        <div class="builtin-grid">
          <div v-for="w in items" :key="w.type" class="builtin-card">
            <div class="builtin-icon">{{ w.icon }}</div>
            <div class="builtin-label">{{ w.label }}</div>
            <div class="builtin-type">{{ w.type }}</div>
            <div class="builtin-props">
              <span v-for="(_, key) in w.schema" :key="key" class="prop-tag">{{ key }}</span>
            </div>
          </div>
        </div>
      </template>
    </section>

    <!-- 新建模板对话框 -->
    <Transition name="fade">
      <div v-if="showCreateDialog" class="dialog-overlay" @click.self="showCreateDialog = false">
        <div class="dialog-panel">
          <div class="dialog-header">
            <h3>新建组件模板</h3>
            <button class="btn-icon" @click="showCreateDialog = false">✕</button>
          </div>
          <div class="dialog-body">
            <div class="form-row">
              <label>模板名称</label>
              <input v-model="newTemplate.name" class="form-input" placeholder="如：销售KPI卡" />
            </div>
            <div class="form-row">
              <label>图标</label>
              <input v-model="newTemplate.icon" class="form-input short" maxlength="2" />
            </div>
            <div class="form-row">
              <label>基础组件</label>
              <select v-model="newTemplate.baseType" class="form-input" @change="onBaseTypeChange">
                <option v-for="w in builtinWidgets" :key="w.type" :value="w.type">{{ w.icon }} {{ w.label }}</option>
              </select>
            </div>
            <div class="form-row">
              <label>说明</label>
              <input v-model="newTemplate.description" class="form-input" placeholder="可选" />
            </div>

            <!-- 预设属性 -->
            <div class="props-section">
              <div class="props-title">预设属性</div>
              <div v-for="(field, key) in currentSchema" :key="key" class="form-row compact">
                <label>{{ field.label || key }}</label>
                <input
                  v-if="field.type === 'string' || field.type === 'color'"
                  v-model="newTemplate.presetProps[key]"
                  class="form-input"
                  :type="field.type === 'color' ? 'color' : 'text'"
                />
                <input
                  v-else-if="field.type === 'number'"
                  v-model.number="newTemplate.presetProps[key]"
                  class="form-input"
                  type="number"
                />
                <select v-else-if="field.type === 'select'" v-model="newTemplate.presetProps[key]" class="form-input">
                  <option v-for="opt in field.options" :key="opt" :value="opt">{{ opt }}</option>
                </select>
                <label v-else-if="field.type === 'boolean'" class="checkbox-row">
                  <input type="checkbox" v-model="newTemplate.presetProps[key]" />
                  <span>{{ newTemplate.presetProps[key] ? '是' : '否' }}</span>
                </label>
              </div>
            </div>
          </div>
          <div class="dialog-footer">
            <button class="btn-cancel" @click="showCreateDialog = false">取消</button>
            <button class="btn-save" @click="saveTemplate" :disabled="!newTemplate.name.trim()">保存模板</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.material-lib-page {
  max-width: 960px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary, #e0e6ff);
  margin: 0;
}

.btn-create {
  padding: 8px 18px;
  border-radius: 8px;
  background: var(--accent, #00d4ff);
  color: #0a0e1a;
  font-weight: 600;
  border: none;
  cursor: pointer;
}

/* AI 快速创建 */
.ai-create-section {
  margin-bottom: 24px;
}

.ai-create-row {
  display: flex;
  gap: 8px;
}

.ai-input {
  flex: 1;
  padding: 10px 16px;
  border-radius: 8px;
  border: 1px solid var(--border-color, #2a2d45);
  background: var(--bg-secondary, #131837);
  color: var(--text-primary, #e0e6ff);
  font-size: 14px;
  outline: none;
}

.ai-input:focus {
  border-color: var(--accent, #00d4ff);
}

.btn-ai {
  padding: 10px 20px;
  border-radius: 8px;
  background: linear-gradient(135deg, #7b61ff, #00d4ff);
  color: #fff;
  font-weight: 600;
  border: none;
  cursor: pointer;
  white-space: nowrap;
}

.btn-ai:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 模板区域 */
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #e0e6ff);
  margin: 24px 0 12px;
}

.template-grid, .builtin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}

.template-card {
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border-color, #2a2d45);
  border-radius: 10px;
  padding: 14px;
}

.tpl-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.tpl-icon { font-size: 20px; }
.tpl-name { font-weight: 600; color: var(--text-primary); }
.tpl-type { font-size: 12px; color: var(--text-secondary, #8892b0); }
.tpl-desc { font-size: 12px; color: var(--text-muted, #4a5578); margin-top: 4px; }

.tpl-actions {
  margin-top: 8px;
  text-align: right;
}

/* 内置组件 */
.category-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--accent, #00d4ff);
  margin: 16px 0 8px;
  padding-left: 4px;
}

.builtin-card {
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border-color, #2a2d45);
  border-radius: 10px;
  padding: 14px;
  text-align: center;
}

.builtin-icon { font-size: 28px; margin-bottom: 6px; }
.builtin-label { font-weight: 600; color: var(--text-primary); font-size: 14px; }
.builtin-type { font-size: 11px; color: var(--text-muted); font-family: monospace; }

.builtin-props {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: center;
}

.prop-tag {
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(0, 212, 255, 0.1);
  color: var(--accent, #00d4ff);
  font-size: 11px;
}

/* 对话框 */
.dialog-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-panel {
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border-color, #2a2d45);
  border-radius: 12px;
  width: 480px;
  max-height: 80vh;
  overflow-y: auto;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color, #2a2d45);
}

.dialog-header h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 16px;
}

.dialog-body {
  padding: 16px 20px;
}

.dialog-footer {
  padding: 12px 20px;
  border-top: 1px solid var(--border-color, #2a2d45);
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.form-row {
  margin-bottom: 12px;
}

.form-row label {
  display: block;
  font-size: 13px;
  color: var(--text-secondary, #8892b0);
  margin-bottom: 4px;
}

.form-row.compact {
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color, #2a2d45);
  background: var(--bg-primary, #0a0e1a);
  color: var(--text-primary, #e0e6ff);
  font-size: 14px;
  outline: none;
}

.form-input.short { width: 60px; }

.form-input:focus {
  border-color: var(--accent, #00d4ff);
}

.props-section {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color, #2a2d45);
}

.props-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 10px;
}

.checkbox-row {
  display: flex !important;
  align-items: center;
  gap: 6px;
}

.btn-sm {
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 12px;
}

.btn-sm.danger {
  border-color: #ff4560;
  color: #ff4560;
}

.btn-save {
  padding: 8px 20px;
  border-radius: 8px;
  background: var(--accent, #00d4ff);
  color: #0a0e1a;
  font-weight: 600;
  border: none;
  cursor: pointer;
}

.btn-save:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-cancel {
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
}

.btn-icon {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 18px;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
