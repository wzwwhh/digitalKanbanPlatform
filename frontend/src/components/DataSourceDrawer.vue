<script setup>
import { ref, computed } from 'vue'
import { useProjectStore } from '../stores/project'
import { useDialog } from '../composables/useDialog'
import { useRouter, useRoute } from 'vue-router'

const props = defineProps({
  visible: { type: Boolean, default: false }
})

const emit = defineEmits(['update:visible'])

const projectStore = useProjectStore()
const { confirm: showConfirm } = useDialog()
const router = useRouter()
const route = useRoute()

const dataSources = computed(() => projectStore.currentProject?.dataSources || [])
const projectId = computed(() => projectStore.currentProject?.id)

// 表单状态
const showForm = ref(false)
const formTab = ref('api')
const probing = ref(false)
const probeResult = ref(null)
const form = ref({ name: '', url: '', method: 'GET', dataPath: '', headers: '', body: '', description: '' })

// 数据库表单
const dbTables = ref([])
const dbForm = ref({ name: '', table: '', sql: '', description: '' })
const dbProbeResult = ref(null)
const dbProbing = ref(false)
const fieldAnnotations = ref({})
const inferring = ref(false)

// Mock 数据源目录
const mockCatalog = ref([])
const showMockPanel = ref(false)
const mockLoading = ref(false)

function closeDrawer() {
  emit('update:visible', false)
  // 重置表单
  showForm.value = false
}

// API 相关
async function probeApi() {
  if (!form.value.url) return
  probing.value = true
  probeResult.value = null
  try {
    const resp = await fetch('/api/data/probe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: form.value.url, method: form.value.method }),
    })
    probeResult.value = await resp.json()
  } catch (err) {
    probeResult.value = { status: -1, fields: [], sample: [], structure: err.message }
  } finally {
    probing.value = false
  }
}

function saveApiDataSource() {
  if (!form.value.name.trim()) form.value.name = `数据源 ${dataSources.value.length + 1}`
  let autoPath = form.value.dataPath || ''
  if (!autoPath && probeResult.value?.structure) {
    const match = probeResult.value.structure.match(/^object\.(\w+)\[\]$/)
    if (match) autoPath = match[1]
  }

  projectStore.addDataSource({
    name: form.value.name.trim(),
    type: 'api',
    url: form.value.url,
    method: form.value.method,
    dataPath: autoPath,
    fields: probeResult.value?.fields || [],
    sample: probeResult.value?.sample?.slice(0, 3) || [],
    structure: probeResult.value?.structure || '',
    createdAt: new Date().toISOString(),
  })

  showForm.value = false
  form.value = { name: '', url: '', method: 'GET', dataPath: '' }
  probeResult.value = null
}

// 数据库相关
async function loadDbTables() {
  try {
    const resp = await fetch('/api/data/db/tables')
    const data = await resp.json()
    if (data.success) {
      dbTables.value = data.tables.filter(t => t !== 'sqlite_sequence')
    }
  } catch (e) {
    console.error('加载表失败', e)
  }
}

async function probeDbTable() {
  if (!dbForm.value.table) return
  dbProbing.value = true
  dbProbeResult.value = null
  try {
    const resp = await fetch('/api/data/db/probe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ table: dbForm.value.table }),
    })
    dbProbeResult.value = await resp.json()
    if (!dbForm.value.sql) dbForm.value.sql = `SELECT * FROM ${dbForm.value.table}`
    if (!dbForm.value.name) dbForm.value.name = dbForm.value.table

    // 自动填充字段注释
    if (dbProbeResult.value?.success) {
      const dbComments = dbProbeResult.value.comments || {}
      const fields = (dbProbeResult.value.fields || []).map(f => f.name)
      const sample = dbProbeResult.value.sample || []

      if (Object.keys(dbComments).length > 0) {
        // MySQL 有 COMMENT：直接用
        fieldAnnotations.value = { ...dbComments }
      } else if (fields.length > 0) {
        // 无注释（SQLite 等）：自动触发 AI 推测
        aiInferFields(fields, sample)
      }
    }
  } catch (e) {
    dbProbeResult.value = { success: false, message: e.message }
  } finally {
    dbProbing.value = false
  }
}

function saveDbDataSource() {
  if (!dbForm.value.name.trim()) dbForm.value.name = `数据库-${dbForm.value.table}`
  const fields = (dbProbeResult.value?.fields || []).map(f => f.name)

  projectStore.addDataSource({
    name: dbForm.value.name.trim(),
    type: 'database',
    table: dbForm.value.table,
    sql: dbForm.value.sql || `SELECT * FROM ${dbForm.value.table}`,
    description: dbForm.value.description || '',
    fields,
    fieldAnnotations: { ...fieldAnnotations.value },
    sample: dbProbeResult.value?.sample?.slice(0, 3) || [],
    rowCount: dbProbeResult.value?.rowCount || 0,
    createdAt: new Date().toISOString(),
  })

  showForm.value = false
  dbForm.value = { name: '', table: '', sql: '', description: '' }
  dbProbeResult.value = null
  fieldAnnotations.value = {}
}

function switchFormTab(tab) {
  formTab.value = tab
  if (tab === 'database' && dbTables.value.length === 0) {
    loadDbTables()
  }
}

async function removeDs(dsId) {
  const ok = await showConfirm('确定删除这个数据源？')
  if (ok) projectStore.removeDataSource(dsId)
}

function cancelForm() {
  showForm.value = false
  probeResult.value = null
  dbProbeResult.value = null
  fieldAnnotations.value = {}
}

async function aiInferFields(fields, sample) {
  inferring.value = true
  try {
    const resp = await fetch('/api/data/infer-fields', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fields, sample: sample?.slice(0, 3) || [] }),
    })
    const data = await resp.json()
    if (data.success && data.annotations) {
      fieldAnnotations.value = { ...fieldAnnotations.value, ...data.annotations }
    }
  } catch { /* ignore */ }
  finally { inferring.value = false }
}

function goToDataSources() {
  closeDrawer()
  if (projectId.value) {
    router.push({ name: 'datasources', params: { projectId: projectId.value } })
  }
}

// Mock 数据源一键添加
async function loadMockCatalog() {
  if (mockCatalog.value.length > 0) {
    showMockPanel.value = true
    return
  }
  mockLoading.value = true
  try {
    const resp = await fetch('/api/mock/catalog')
    mockCatalog.value = await resp.json()
  } catch (e) {
    console.error('加载 Mock 目录失败', e)
  } finally {
    mockLoading.value = false
    showMockPanel.value = true
  }
}

function addMockDataSource(item) {
  // 检查是否已添加
  const existing = dataSources.value.find(d => d.url === item.url)
  if (existing) return

  projectStore.addDataSource({
    name: item.name,
    type: 'api',
    url: item.url,
    method: item.method,
    dataPath: item.dataPath,
    fields: item.fields,
    fieldAnnotations: item.fieldAnnotations || {},
    sample: item.sample || [],
    description: item.description || '',
    isMock: true,
    createdAt: new Date().toISOString(),
  })
}

function addAllMockDataSources() {
  let count = 0
  for (const item of mockCatalog.value) {
    const existing = dataSources.value.find(d => d.url === item.url)
    if (!existing) {
      addMockDataSource(item)
      count++
    }
  }
  if (count > 0) showMockPanel.value = false
}

function isMockAdded(item) {
  return dataSources.value.some(d => d.url === item.url)
}
</script>

<template>
  <Transition name="drawer">
    <div class="ds-drawer-overlay" v-if="visible" @click.self="closeDrawer">
      <aside class="ds-drawer">
        <div class="drawer-header">
          <span>⚡ 数据源管理</span>
          <button class="btn-icon" @click="closeDrawer">✕</button>
        </div>

        <div class="drawer-body">
          <!-- 列表视图 -->
          <template v-if="!showForm">
            <div class="drawer-actions">
              <button class="btn-add" @click="showForm = true">＋ 添加数据源</button>
              <button class="btn-link" @click="goToDataSources">全屏管理页</button>
            </div>

            <!-- Mock 数据源快捷入口 -->
            <button class="btn-mock" @click="loadMockCatalog" :disabled="mockLoading">
              {{ mockLoading ? '加载中...' : '📦 使用示例数据源' }}
            </button>

            <!-- Mock 选择面板 -->
            <div v-if="showMockPanel && mockCatalog.length > 0" class="mock-panel">
              <div class="mock-header">
                <span>选择示例数据源</span>
                <button class="btn-icon" @click="showMockPanel = false">✕</button>
              </div>
              <div v-for="item in mockCatalog" :key="item.url" class="mock-item" :class="{ added: isMockAdded(item) }">
                <div class="mock-info">
                  <div class="mock-name">{{ item.icon }} {{ item.name }}</div>
                  <div class="mock-desc">{{ item.description }}</div>
                  <div class="mock-fields">
                    <span v-for="f in item.fields.slice(0, 4)" :key="f" class="drawer-field">{{ item.fieldAnnotations?.[f] ? `${f}(${item.fieldAnnotations[f]})` : f }}</span>
                    <span v-if="item.fields.length > 4" class="drawer-field-more">+{{ item.fields.length - 4 }}</span>
                  </div>
                </div>
                <button v-if="!isMockAdded(item)" class="btn-add-mock" @click="addMockDataSource(item)">添加</button>
                <span v-else class="mock-added-tag">✅ 已添加</span>
              </div>
              <button class="btn-add-all" @click="addAllMockDataSources">一键全部添加</button>
            </div>

            <div v-if="dataSources.length > 0" class="ds-list">
              <div v-for="ds in dataSources" :key="ds.id" class="drawer-ds-card">
                <div class="card-header">
                  <div class="ds-name">{{ ds.name }}</div>
                  <button class="btn-icon danger" @click="removeDs(ds.id)" title="删除">✕</button>
                </div>
                <div class="ds-type" :class="{ 'type-db': ds.type === 'database' }">
                  {{ ds.type === 'database' ? '数据库' : 'API' }}
                </div>
                <div class="ds-url" v-if="ds.type === 'api'">{{ ds.url }}</div>
                <div class="ds-url" v-else>📋 {{ ds.table }}</div>
                <div class="drawer-ds-fields">
                  <span v-for="f in (ds.fields || []).slice(0, 5)" :key="f" class="drawer-field">{{ f }}</span>
                  <span v-if="(ds.fields || []).length > 5" class="drawer-field-more">+{{ ds.fields.length - 5 }}</span>
                </div>
              </div>
            </div>
            <div v-else class="drawer-empty">
              <p>暂无数据源</p>
            </div>
          </template>

          <!-- 表单视图 -->
          <template v-else>
            <div class="form-view">
              <div class="source-tabs">
                <button :class="['tab-btn', { active: formTab === 'api' }]" @click="switchFormTab('api')">🔗 API</button>
                <button :class="['tab-btn', { active: formTab === 'database' }]" @click="switchFormTab('database')">🗄️ 数据库</button>
              </div>

              <!-- API -->
              <div v-if="formTab === 'api'" class="form-container">
                <input v-model="form.name" placeholder="名称(如:销售数据)" class="form-input" />
                <div class="url-row">
                  <select v-model="form.method" class="method-select"><option>GET</option><option>POST</option></select>
                  <input v-model="form.url" placeholder="https://api..." class="form-input flex-1" />
                </div>
                <button class="btn-probe full" @click="probeApi" :disabled="probing || !form.url">
                  {{ probing ? '探测中...' : '🔍 探测 API' }}
                </button>

                <div v-if="probeResult" class="probe-result mini">
                  <div v-if="probeResult.status === 200 || probeResult.fields?.length" class="probe-success">
                    <div>✅ 探测成功: 发现 {{ probeResult.fields?.length || 0 }} 字段</div>
                  </div>
                  <div v-else class="probe-fail">❌ 探测失败: {{ probeResult.structure || '无法连接' }}</div>
                </div>
                <div class="form-actions">
                  <button class="btn-save" @click="saveApiDataSource" :disabled="!probeResult || probeResult.status === -1">保存</button>
                  <button class="btn-cancel" @click="cancelForm">取消</button>
                </div>
              </div>

              <!-- 数据库 -->
              <div v-if="formTab === 'database'" class="form-container">
                <input v-model="dbForm.name" placeholder="名称(如:销售库)" class="form-input" />
                <select v-model="dbForm.table" class="form-input" @change="probeDbTable">
                  <option value="" disabled>请选择表...</option>
                  <option v-for="t in dbTables" :key="t" :value="t">{{ t }}</option>
                </select>
                <textarea v-if="dbProbeResult?.success" v-model="dbForm.sql" class="form-input sql-input" rows="2" placeholder="SELECT * FROM ..."></textarea>
                
                <button v-if="!dbProbeResult?.success" class="btn-probe full" @click="probeDbTable" :disabled="dbProbing || !dbForm.table">
                  {{ dbProbing ? '探测中...' : '🔍 探测表' }}
                </button>

                <div v-if="dbProbeResult" class="probe-result mini">
                  <div v-if="dbProbeResult.success" class="probe-success">✅ 探测成功: {{ dbProbeResult.rowCount }} 行数据</div>
                  <div v-else class="probe-fail">❌ 探测失败: {{ dbProbeResult.message }}</div>
                </div>
                <div class="form-actions">
                  <button class="btn-save" @click="saveDbDataSource" :disabled="!dbProbeResult?.success">保存</button>
                  <button class="btn-cancel" @click="cancelForm">取消</button>
                </div>
              </div>
            </div>
          </template>
        </div>
      </aside>
    </div>
  </Transition>
</template>

<style scoped>
/* Drawer 基础样式继承自 AppLayout.vue 的全局部分，这里补充独立样式 */
.ds-drawer-overlay {
  position: fixed;
  top: 0; right: 0; bottom: 0; left: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 1000;
}

.ds-drawer {
  position: absolute;
  top: 0; right: 0; bottom: 0;
  width: 340px;
  background: var(--bg-primary, #0a0e1a);
  border-left: 1px solid var(--border-color, #2a2d45);
  display: flex;
  flex-direction: column;
}

.drawer-header {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px solid var(--border-color, #2a2d45);
  font-weight: 600;
  color: var(--text-primary, #e0e6ff);
}

.drawer-body {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.drawer-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.btn-add {
  padding: 6px 12px;
  background: var(--accent, #00d4ff);
  color: #0a0e1a;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  font-size: 13px;
}

.btn-link {
  background: none;
  border: none;
  color: var(--text-secondary, #8892b0);
  cursor: pointer;
  font-size: 13px;
  text-decoration: underline;
}

.drawer-ds-card {
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border-color, #2a2d45);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 4px;
}

.ds-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
}

.ds-type {
  display: inline-block;
  padding: 2px 6px;
  background: rgba(0, 212, 255, 0.1);
  color: var(--accent, #00d4ff);
  border-radius: 4px;
  font-size: 11px;
  margin-bottom: 8px;
}

.ds-type.type-db {
  background: rgba(123, 97, 255, 0.1);
  color: #7b61ff;
}

.ds-url {
  font-size: 12px;
  color: var(--text-muted);
  word-break: break-all;
  margin-bottom: 8px;
}

.drawer-ds-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.drawer-field {
  padding: 2px 6px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  font-size: 11px;
  color: var(--text-secondary);
}

.drawer-field-more {
  font-size: 11px;
  color: var(--text-muted);
}

.drawer-empty {
  text-align: center;
  padding: 40px 0;
  color: var(--text-muted);
  font-size: 13px;
}

/* 表单样式 */
.source-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.tab-btn {
  flex: 1;
  padding: 6px;
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.tab-btn.active {
  background: var(--accent);
  color: #0a0e1a;
  border-color: var(--accent);
  font-weight: 600;
}

.form-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-input {
  width: 100%;
  padding: 8px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
}

.url-row {
  display: flex;
  gap: 8px;
}

.method-select {
  padding: 8px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-primary);
}

.flex-1 { flex: 1; }

.btn-probe.full {
  width: 100%;
  padding: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.probe-result.mini {
  font-size: 12px;
  padding: 8px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
}

.probe-success { color: #00e396; }
.probe-fail { color: #ff4560; }

.form-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.btn-save {
  flex: 1;
  padding: 8px;
  background: var(--accent);
  color: #0a0e1a;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}

.btn-save:disabled { opacity: 0.5; }

.btn-cancel {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  border-radius: 6px;
  cursor: pointer;
}

.btn-icon {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 16px;
}

.btn-icon.danger:hover { color: #ff4560; }

/* Mock 数据源样式 */
.btn-mock {
  width: 100%;
  padding: 8px;
  margin-bottom: 16px;
  background: linear-gradient(135deg, rgba(123, 97, 255, 0.1), rgba(0, 212, 255, 0.1));
  border: 1px dashed rgba(123, 97, 255, 0.4);
  border-radius: 8px;
  color: #7b61ff;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-mock:hover {
  background: linear-gradient(135deg, rgba(123, 97, 255, 0.2), rgba(0, 212, 255, 0.15));
  border-color: #7b61ff;
}

.mock-panel {
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border-color, #2a2d45);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
}
.mock-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 10px;
}
.mock-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 8px;
  background: rgba(255,255,255,0.03);
  border: 1px solid transparent;
  transition: all 0.15s;
}
.mock-item:hover:not(.added) {
  border-color: var(--border-color);
  background: rgba(255,255,255,0.06);
}
.mock-item.added {
  opacity: 0.6;
}
.mock-info { flex: 1; min-width: 0; }
.mock-name { font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 2px; }
.mock-desc { font-size: 11px; color: var(--text-muted); margin-bottom: 4px; }
.mock-fields { display: flex; flex-wrap: wrap; gap: 3px; }
.btn-add-mock {
  padding: 4px 10px;
  background: var(--accent, #00d4ff);
  color: #0a0e1a;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  flex-shrink: 0;
}
.mock-added-tag { font-size: 12px; color: #00e396; flex-shrink: 0; }
.btn-add-all {
  width: 100%;
  padding: 6px;
  background: linear-gradient(135deg, #7b61ff, #00d4ff);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 4px;
}

/* 动画 */
.drawer-enter-active, .drawer-leave-active { transition: all 0.3s ease; }
.drawer-enter-from .ds-drawer, .drawer-leave-to .ds-drawer { transform: translateX(100%); }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
</style>
