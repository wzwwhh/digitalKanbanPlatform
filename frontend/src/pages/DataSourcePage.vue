<script setup>
import { ref, computed } from 'vue'
import { useProjectStore } from '../stores/project'
import { useRoute } from 'vue-router'
import { useDialog } from '../composables/useDialog'

const route = useRoute()
const projectStore = useProjectStore()
const { confirm: showConfirm } = useDialog()

const projectId = computed(() => route.params.projectId)
const dataSources = computed(() => projectStore.currentProject?.dataSources || [])

// 表单状态
const showForm = ref(false)
const formTab = ref('api')  // 'api' | 'database'
const probing = ref(false)
const probeResult = ref(null)
const form = ref({
  name: '',
  url: '',
  method: 'GET',
  dataPath: '',
  headers: '',   // 自定义请求头 JSON
  body: '',      // POST 请求体 JSON
  description: '',
})

// 字段注释（临时编辑用）
const fieldAnnotations = ref({})
const editingDsId = ref(null)

// 数据库表单
const dbTables = ref([])
const dbForm = ref({
  name: '',
  table: '',
  sql: '',
  description: '',
})
const dbInfo = ref(null)
const dbProbeResult = ref(null)
const dbProbing = ref(false)

// 自定义数据库连接
const customDbMode = ref(false)
const customDb = ref({
  dbType: 'sqlite',
  dbPath: '',
  host: 'localhost',
  port: 3306,
  user: 'root',
  password: '',
  database: '',
})
const customConnecting = ref(false)

// AI 字段推测
const inferring = ref(false)

// 内置 Mock 数据源
const mockSources = [
  { label: '📊 模拟销售数据', url: '/api/mock/sales', desc: '月度×品类：sales, revenue, orders' },
  { label: '👥 模拟用户统计', url: '/api/mock/users', desc: '日PV/UV + 渠道分布' },
  { label: '📦 模拟订单列表', url: '/api/mock/orders', desc: '订单ID、产品、金额、状态' },
  { label: '🎯 模拟KPI汇总', url: '/api/mock/kpi', desc: '今日订单、营收、转化率等' },
]

function useMockSource(mock) {
  form.value.name = mock.label.replace(/^[^\s]+\s/, '')
  form.value.url = mock.url
  form.value.method = 'GET'
  form.value.dataPath = ''
  showForm.value = true
  probeResult.value = null
}

async function probeApi() {
  if (!form.value.url) return
  probing.value = true
  probeResult.value = null

  try {
    const resp = await fetch('/api/data/probe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: form.value.url,
        method: form.value.method,
      }),
    })
    probeResult.value = await resp.json()
  } catch (err) {
    probeResult.value = { status: -1, fields: [], sample: [], structure: err.message }
  } finally {
    probing.value = false
  }
}

function saveDataSource() {
  if (!form.value.name.trim()) {
    form.value.name = `数据源 ${dataSources.value.length + 1}`
  }

  // 从探测结构中自动推断 dataPath（如 "object.data[]" → "data"）
  let autoPath = form.value.dataPath || ''
  if (!autoPath && probeResult.value?.structure) {
    const match = probeResult.value.structure.match(/^object\.(\w+)\[\]$/)
    if (match) autoPath = match[1]
  }

  // 解析自定义 headers
  let parsedHeaders = null
  if (form.value.headers.trim()) {
    try { parsedHeaders = JSON.parse(form.value.headers) } catch { parsedHeaders = null }
  }
  let parsedBody = null
  if (form.value.body.trim()) {
    try { parsedBody = JSON.parse(form.value.body) } catch { parsedBody = form.value.body }
  }

  const ds = {
    name: form.value.name.trim(),
    type: 'api',
    url: form.value.url,
    method: form.value.method,
    dataPath: autoPath,
    headers: parsedHeaders,
    body: parsedBody,
    description: form.value.description,
    fields: probeResult.value?.fields || [],
    fieldAnnotations: { ...fieldAnnotations.value },
    sample: probeResult.value?.sample?.slice(0, 3) || [],
    structure: probeResult.value?.structure || '',
    createdAt: new Date().toISOString(),
  }

  projectStore.addDataSource(ds)

  // 重置
  showForm.value = false
  form.value = { name: '', url: '', method: 'GET', dataPath: '', headers: '', body: '', description: '' }
  probeResult.value = null
  fieldAnnotations.value = {}
}

async function removeDs(dsId) {
  const ok = await showConfirm('确定删除这个数据源？')
  if (ok) {
    projectStore.removeDataSource(dsId)
  }
}

function cancelForm() {
  showForm.value = false
  probeResult.value = null
  dbProbeResult.value = null
  formTab.value = 'api'
}

// ========== 数据库相关 ==========

async function loadDbTables() {
  try {
    const resp = await fetch('/api/data/db/tables')
    const data = await resp.json()
    if (data.success) {
      dbTables.value = data.tables.filter(t => t !== 'sqlite_sequence')
    }
  } catch (e) {
    console.error('加载表列表失败', e)
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
    // 自动生成默认 SQL
    if (!dbForm.value.sql) {
      dbForm.value.sql = `SELECT * FROM ${dbForm.value.table}`
    }
    if (!dbForm.value.name) {
      dbForm.value.name = dbForm.value.table
    }
  } catch (e) {
    dbProbeResult.value = { success: false, message: e.message }
  } finally {
    dbProbing.value = false
  }
}

function saveDbDataSource() {
  if (!dbForm.value.name.trim()) {
    dbForm.value.name = `数据库-${dbForm.value.table}`
  }

  const fieldsRaw = dbProbeResult.value?.fields || []
  const fields = fieldsRaw.map(f => f.name)
  // 自动生成字段注释（来自数据库类型信息）
  const autoAnnotations = {}
  fieldsRaw.forEach(f => { autoAnnotations[f.name] = f.type || '' })

  const ds = {
    name: dbForm.value.name.trim(),
    type: 'database',
    table: dbForm.value.table,
    sql: dbForm.value.sql || `SELECT * FROM ${dbForm.value.table}`,
    description: dbForm.value.description,
    dbPath: dbInfo.value?.path || 'sample_data.db',
    dbType: 'SQLite',
    fields,
    fieldAnnotations: { ...autoAnnotations, ...fieldAnnotations.value },
    sample: dbProbeResult.value?.sample?.slice(0, 3) || [],
    rowCount: dbProbeResult.value?.rowCount || 0,
    createdAt: new Date().toISOString(),
  }

  projectStore.addDataSource(ds)

  // 重置
  showForm.value = false
  dbForm.value = { name: '', table: '', sql: '', description: '' }
  dbProbeResult.value = null
  fieldAnnotations.value = {}
  formTab.value = 'api'
}

function switchFormTab(tab) {
  formTab.value = tab
  if (tab === 'database' && dbTables.value.length === 0) {
    loadDbTables()
    loadDbInfo()
  }
}

async function loadDbInfo() {
  try {
    const resp = await fetch('/api/data/db/tables')
    const data = await resp.json()
    if (data.success) {
      dbInfo.value = { path: data.dbPath || 'sample_data.db', tables: data.tables?.length || 0 }
    }
  } catch { /* ignore */ }
}

// 字段注释编辑
function startEditAnnotations(ds) {
  editingDsId.value = ds.id
  fieldAnnotations.value = { ...(ds.fieldAnnotations || {}) }
}

function saveAnnotations(ds) {
  projectStore.updateDataSource(ds.id, { fieldAnnotations: { ...fieldAnnotations.value } })
  editingDsId.value = null
  fieldAnnotations.value = {}
}

function cancelEditAnnotations() {
  editingDsId.value = null
  fieldAnnotations.value = {}
}

// 自定义数据库连接
async function connectCustomDb() {
  customConnecting.value = true
  try {
    const resp = await fetch('/api/data/db/connect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(customDb.value),
    })
    const data = await resp.json()
    if (data.success) {
      dbTables.value = data.tables
      dbInfo.value = { path: data.dbPath, tables: data.tables.length, type: data.dbType }
    } else {
      alert('连接失败: ' + (data.message || '未知错误'))
    }
  } catch (e) {
    alert('连接失败: ' + e.message)
  } finally {
    customConnecting.value = false
  }
}

// AI 智能推测字段含义
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

// 数据源导出 JSON
function exportDataSources() {
  const data = JSON.stringify(dataSources.value, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'datasources.json'
  a.click()
  URL.revokeObjectURL(url)
}

// 数据源导入 JSON
function importDataSources() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const text = await file.text()
    try {
      const list = JSON.parse(text)
      if (!Array.isArray(list)) { alert('格式错误：需要 JSON 数组'); return }
      list.forEach(ds => {
        const { id, ...rest } = ds
        projectStore.addDataSource(rest)
      })
      alert(`成功导入 ${list.length} 个数据源`)
    } catch { alert('JSON 解析失败') }
  }
  input.click()
}

// 数据源跨项目复制
async function copyFromOtherProject() {
  const otherProjects = projectStore.projects.filter(p => p.id !== projectStore.currentProject?.id)
  if (otherProjects.length === 0) {
    alert('没有其他可用的项目。')
    return
  }
  
  const options = otherProjects.map((p, i) => `${i + 1}. ${p.name} (${p.dataSources?.length || 0} 个数据源)`).join('\n')
  const choice = prompt(`请选择要从中复制数据源的项目编号：\n\n${options}\n\n输入编号（如 1）：`)
  
  if (!choice) return
  const index = parseInt(choice, 10) - 1
  if (index >= 0 && index < otherProjects.length) {
    const fromProj = otherProjects[index]
    const count = projectStore.copyDataSources(fromProj.id)
    if (count > 0) {
      alert(`成功复制了 ${count} 个数据源！`)
    } else {
      alert('没有可复制的数据源或数据源已存在。')
    }
  } else {
    alert('无效的编号。')
  }
}
</script>

<template>
  <div class="datasource-page">
    <div class="page-header">
      <h1>数据源管理</h1>
      <div class="header-actions">
        <button class="btn-sm" @click="copyFromOtherProject" title="从其他项目复制">📋 复制跨项目</button>
        <button class="btn-sm" @click="importDataSources" title="从 JSON 导入">📥 导入</button>
        <button class="btn-sm" @click="exportDataSources" v-if="dataSources.length" title="导出为 JSON">📤 导出</button>
        <button class="btn-add" @click="showForm = true" v-if="!showForm">＋ 添加数据源</button>
      </div>
    </div>

    <!-- Tab 切换 -->
    <div class="source-tabs" v-if="showForm">
      <button :class="['tab-btn', { active: formTab === 'api' }]" @click="switchFormTab('api')">🔗 API 数据源</button>
      <button :class="['tab-btn', { active: formTab === 'database' }]" @click="switchFormTab('database')">🗄️ 数据库</button>
    </div>

    <!-- 内置 Mock 数据源 -->
    <section class="mock-section" v-if="!showForm && dataSources.length === 0">
      <div class="section-title">🚀 快速开始 — 使用内置模拟数据</div>
      <div class="mock-grid">
        <div
          v-for="mock in mockSources"
          :key="mock.url"
          class="mock-card"
          @click="useMockSource(mock)"
        >
          <div class="mock-label">{{ mock.label }}</div>
          <div class="mock-desc">{{ mock.desc }}</div>
          <div class="mock-url">{{ mock.url }}</div>
        </div>
      </div>
    </section>

    <!-- 添加表单 -->
    <!-- API 表单 -->
    <section class="form-section" v-if="showForm && formTab === 'api'">
      <div class="section-title">配置数据源</div>

      <div class="form-row">
        <label>名称</label>
        <input v-model="form.name" placeholder="如：销售数据" class="form-input" />
      </div>

      <div class="form-row">
        <label>API 地址</label>
        <div class="url-row">
          <select v-model="form.method" class="method-select">
            <option value="GET">GET</option>
            <option value="POST">POST</option>
          </select>
          <input v-model="form.url" placeholder="https://api.example.com/data" class="form-input flex-1" />
          <button class="btn-probe" @click="probeApi" :disabled="probing || !form.url">
            {{ probing ? '探测中...' : '🔍 探测' }}
          </button>
        </div>
      </div>

      <div class="form-row">
        <label>请求头 Headers <small class="hint">（JSON 格式，可选）</small></label>
        <textarea v-model="form.headers" class="form-input code-input" rows="2" placeholder='{"Authorization": "Bearer xxx"}'></textarea>
      </div>

      <div class="form-row" v-if="form.method === 'POST'">
        <label>请求体 Body <small class="hint">（JSON 格式，可选）</small></label>
        <textarea v-model="form.body" class="form-input code-input" rows="2" placeholder='{"page": 1, "size": 100}'></textarea>
      </div>

      <div class="form-row">
        <label>数据路径 dataPath <small class="hint">（JSON 中数据数组的路径，如 "data"，可留空自动推断）</small></label>
        <input v-model="form.dataPath" placeholder="data" class="form-input" />
      </div>

      <div class="form-row">
        <label>备注说明</label>
        <input v-model="form.description" placeholder="如：每日更新的销售数据接口" class="form-input" />
      </div>

      <!-- 探测结果 -->
      <div v-if="probeResult" class="probe-result">
        <div v-if="probeResult.status === 200 || probeResult.fields?.length" class="probe-success">
          <div class="probe-header">
            <span class="status-badge success">✅ 探测成功</span>
            <span class="structure-tag">{{ probeResult.structure }}</span>
          </div>

          <div class="fields-section">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
              <span class="fields-title" style="margin:0;">发现 {{ probeResult.fields?.length || 0 }} 个字段</span>
              <button class="btn-sm" @click="aiInferFields(probeResult.fields, probeResult.sample)" :disabled="inferring">
                {{ inferring ? '推测中...' : '🤖 AI 推测含义' }}
              </button>
            </div>
            <div class="fields-list">
              <span v-for="f in probeResult.fields" :key="f" class="field-tag">
                {{ f }}<small v-if="fieldAnnotations[f]" style="opacity:0.6;margin-left:4px;">({{ fieldAnnotations[f] }})</small>
              </span>
            </div>
          </div>

          <div class="sample-section" v-if="probeResult.sample?.length">
            <div class="fields-title">示例数据（前 {{ Math.min(probeResult.sample.length, 3) }} 条）</div>
            <pre class="sample-json">{{ JSON.stringify(probeResult.sample.slice(0, 3), null, 2) }}</pre>
          </div>
        </div>

        <div v-else class="probe-fail">
          <span class="status-badge fail">❌ 探测失败</span>
          <span>{{ probeResult.structure || '无法连接' }}</span>
        </div>
      </div>

      <div class="form-actions">
        <button class="btn-save" @click="saveDataSource" :disabled="!probeResult || probeResult.status === -1">
          💾 保存数据源
        </button>
        <button class="btn-cancel" @click="cancelForm">取消</button>
      </div>
    </section>

    <!-- 数据库表单 -->
    <section class="form-section" v-if="showForm && formTab === 'database'">
      <div class="section-title">连接数据库</div>

      <!-- 数据库连接信息 -->
      <div class="db-info-bar" v-if="dbInfo">
        <span class="db-info-item">🗄️ {{ dbInfo.type || 'SQLite' }}</span>
        <span class="db-info-item">📂 {{ dbInfo.path }}</span>
        <span class="db-info-item">📋 {{ dbInfo.tables }} 张表</span>
      </div>

      <!-- 自定义连接切换 -->
      <div class="form-row">
        <label style="display:flex;align-items:center;gap:8px;cursor:pointer;">
          <input type="checkbox" v-model="customDbMode" /> 使用自定义数据库连接
        </label>
      </div>

      <!-- 自定义连接表单 -->
      <div v-if="customDbMode" class="form-section" style="margin-bottom:12px;">
        <div class="form-row">
          <label>数据库类型</label>
          <select v-model="customDb.dbType" class="form-input" style="width:120px;">
            <option value="sqlite">SQLite</option>
            <option value="mysql">MySQL</option>
          </select>
        </div>
        <template v-if="customDb.dbType === 'sqlite'">
          <div class="form-row">
            <label>文件路径</label>
            <input v-model="customDb.dbPath" class="form-input" placeholder="如 /path/to/my.db" />
          </div>
        </template>
        <template v-else>
          <div class="form-row url-row">
            <div class="flex-1">
              <label>主机</label>
              <input v-model="customDb.host" class="form-input" placeholder="localhost" />
            </div>
            <div style="width:80px;">
              <label>端口</label>
              <input v-model.number="customDb.port" class="form-input" placeholder="3306" />
            </div>
          </div>
          <div class="form-row url-row">
            <div class="flex-1">
              <label>用户名</label>
              <input v-model="customDb.user" class="form-input" placeholder="root" />
            </div>
            <div class="flex-1">
              <label>密码</label>
              <input v-model="customDb.password" class="form-input" type="password" placeholder="密码" />
            </div>
          </div>
          <div class="form-row">
            <label>数据库名</label>
            <input v-model="customDb.database" class="form-input" placeholder="my_database" />
          </div>
        </template>
        <button class="btn-probe" @click="connectCustomDb" :disabled="customConnecting">
          {{ customConnecting ? '连接中...' : '🔌 测试连接' }}
        </button>
      </div>

      <div class="form-row">
        <label>名称</label>
        <input v-model="dbForm.name" placeholder="如：销售数据库" class="form-input" />
      </div>

      <div class="form-row">
        <label>选择表</label>
        <div class="url-row">
          <select v-model="dbForm.table" class="form-input flex-1" @change="probeDbTable">
            <option value="" disabled>请选择...</option>
            <option v-for="t in dbTables" :key="t" :value="t">{{ t }}</option>
          </select>
          <button class="btn-probe" @click="probeDbTable" :disabled="dbProbing || !dbForm.table">
            {{ dbProbing ? '探测中...' : '🔍 探测' }}
          </button>
        </div>
      </div>

      <div class="form-row" v-if="dbProbeResult?.success">
        <label>SQL 查询（可选自定义）</label>
        <textarea v-model="dbForm.sql" class="form-input sql-input" rows="3" placeholder="SELECT * FROM ..."></textarea>
      </div>

      <div class="form-row">
        <label>备注说明</label>
        <input v-model="dbForm.description" placeholder="如：主要存储月度销售汇总数据" class="form-input" />
      </div>

      <!-- 探测结果 -->
      <div v-if="dbProbeResult" class="probe-result">
        <div v-if="dbProbeResult.success" class="probe-success">
          <div class="probe-header">
            <span class="status-badge success">✅ 探测成功</span>
            <span class="structure-tag">{{ dbProbeResult.rowCount }} 行数据</span>
          </div>
          <div class="fields-section">
            <div class="fields-title">发现 {{ dbProbeResult.fields?.length || 0 }} 个字段</div>
            <div class="fields-list">
              <span v-for="f in dbProbeResult.fields" :key="f.name" class="field-tag">{{ f.name }} <small>({{ f.type }})</small></span>
            </div>
          </div>
          <div class="sample-section" v-if="dbProbeResult.sample?.length">
            <div class="fields-title">示例数据（前 {{ Math.min(dbProbeResult.sample.length, 3) }} 条）</div>
            <pre class="sample-json">{{ JSON.stringify(dbProbeResult.sample.slice(0, 3), null, 2) }}</pre>
          </div>
        </div>
        <div v-else class="probe-fail">
          <span class="status-badge fail">❌ 探测失败</span>
          <span>{{ dbProbeResult.message || '无法连接' }}</span>
        </div>
      </div>

      <div class="form-actions">
        <button class="btn-save" @click="saveDbDataSource" :disabled="!dbProbeResult?.success">
          💾 保存数据源
        </button>
        <button class="btn-cancel" @click="cancelForm">取消</button>
      </div>
    </section>

    <!-- 已有数据源列表 -->
    <section class="ds-list" v-if="dataSources.length > 0">
      <div class="section-title">已添加的数据源（{{ dataSources.length }}）</div>
      <div class="ds-grid">
      <div v-for="ds in dataSources" :key="ds.id" class="ds-card">
          <div class="ds-card-header">
            <span class="ds-name">{{ ds.name }}</span>
            <span class="ds-type" :class="{ 'type-db': ds.type === 'database' }">{{ ds.type === 'database' ? '数据库' : 'API' }}</span>
          </div>

          <!-- 描述 -->
          <div class="ds-desc" v-if="ds.description">{{ ds.description }}</div>

          <!-- API 详情 -->
          <template v-if="ds.type === 'api'">
            <div class="ds-detail-row">
              <span class="detail-label">{{ ds.method || 'GET' }}</span>
              <span class="detail-value mono">{{ ds.url }}</span>
            </div>
            <div class="ds-detail-row" v-if="ds.headers">
              <span class="detail-label">Headers</span>
              <span class="detail-value mono">{{ JSON.stringify(ds.headers) }}</span>
            </div>
            <div class="ds-detail-row" v-if="ds.body">
              <span class="detail-label">Body</span>
              <span class="detail-value mono">{{ typeof ds.body === 'string' ? ds.body : JSON.stringify(ds.body) }}</span>
            </div>
            <div class="ds-detail-row" v-if="ds.dataPath">
              <span class="detail-label">dataPath</span>
              <span class="detail-value mono">{{ ds.dataPath }}</span>
            </div>
          </template>

          <!-- 数据库详情 -->
          <template v-if="ds.type === 'database'">
            <div class="ds-detail-row">
              <span class="detail-label">{{ ds.dbType || 'SQLite' }}</span>
              <span class="detail-value mono">{{ ds.dbPath || '-' }}</span>
            </div>
            <div class="ds-detail-row">
              <span class="detail-label">表</span>
              <span class="detail-value mono">{{ ds.table }}</span>
            </div>
            <div class="ds-detail-row">
              <span class="detail-label">SQL</span>
              <span class="detail-value mono">{{ ds.sql }}</span>
            </div>
            <div class="ds-detail-row" v-if="ds.rowCount">
              <span class="detail-label">行数</span>
              <span class="detail-value">{{ ds.rowCount }}</span>
            </div>
          </template>

          <!-- 字段列表 + 注释 -->
          <div class="ds-fields-section">
            <div class="fields-header">
              <span class="fields-title">字段（{{ (ds.fields || []).length }}）</span>
              <button v-if="editingDsId !== ds.id" class="btn-sm" @click="startEditAnnotations(ds)">✏️ 编辑注释</button>
              <template v-else>
                <button class="btn-sm" @click="saveAnnotations(ds)">💾 保存</button>
                <button class="btn-sm" @click="cancelEditAnnotations">取消</button>
              </template>
            </div>

            <!-- 查看模式 -->
            <div class="fields-table" v-if="editingDsId !== ds.id">
              <div v-for="f in (ds.fields || [])" :key="f" class="field-row">
                <span class="field-tag">{{ f }}</span>
                <span class="field-annotation" v-if="(ds.fieldAnnotations || {})[f]">{{ ds.fieldAnnotations[f] }}</span>
              </div>
            </div>

            <!-- 编辑模式 -->
            <div class="fields-table editing" v-else>
              <div v-for="f in (ds.fields || [])" :key="f" class="field-row">
                <span class="field-tag">{{ f }}</span>
                <input
                  class="annotation-input"
                  v-model="fieldAnnotations[f]"
                  :placeholder="'如：月份、销售额...'"
                />
              </div>
            </div>
          </div>

          <div class="ds-actions">
            <button class="btn-sm" @click="useMockSource({ label: ds.name, url: ds.url })">重新探测</button>
            <button class="btn-sm danger" @click="removeDs(ds.id)">删除</button>
          </div>
        </div>
      </div>

      <!-- 没有表单打开时显示添加按钮 -->
      <div class="add-more" v-if="!showForm">
        <button class="btn-add-more" @click="showForm = true">＋ 添加更多数据源</button>
        <div class="mock-hint">
          或使用内置模拟数据：
          <span
            v-for="mock in mockSources"
            :key="mock.url"
            class="mock-link"
            @click="useMockSource(mock)"
          >{{ mock.label }}</span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.datasource-page {
  max-width: 860px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary, #e0e6ff);
  margin: 0;
}

.btn-add {
  padding: 8px 18px;
  background: linear-gradient(135deg, #7b61ff, #00d4ff);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #e0e6ff);
  margin-bottom: 14px;
}

/* Mock 数据源卡片 */
.mock-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.mock-card {
  padding: 16px;
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.mock-card:hover {
  border-color: var(--accent, #00d4ff);
  transform: translateY(-1px);
}

.mock-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #e0e6ff);
  margin-bottom: 4px;
}

.mock-desc {
  font-size: 12px;
  color: var(--text-muted, #4a5578);
  margin-bottom: 8px;
}

.mock-url {
  font-size: 11px;
  color: var(--accent, #00d4ff);
  font-family: monospace;
  opacity: 0.7;
}

/* 表单 */
.form-section {
  padding: 20px 24px;
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 12px;
  margin-bottom: 24px;
}

.form-row {
  margin-bottom: 14px;
}

.form-row label {
  display: block;
  font-size: 13px;
  color: var(--text-secondary, #8892b0);
  margin-bottom: 6px;
}

.form-input {
  width: 100%;
  padding: 8px 12px;
  background: var(--bg-tertiary, #1a2045);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 8px;
  color: var(--text-primary, #e0e6ff);
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
}

.form-input:focus {
  border-color: var(--accent, #00d4ff);
}

.url-row {
  display: flex;
  gap: 8px;
}

.method-select {
  width: 80px;
  padding: 8px;
  background: var(--bg-tertiary, #1a2045);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 8px;
  color: var(--text-primary, #e0e6ff);
  font-size: 13px;
}

.flex-1 { flex: 1; }

.btn-probe {
  padding: 8px 16px;
  background: var(--accent, #00d4ff);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
}

.btn-probe:disabled {
  opacity: 0.5;
  cursor: default;
}

/* 探测结果 */
.probe-result {
  margin: 16px 0;
  padding: 14px;
  background: var(--bg-tertiary, #1a2045);
  border-radius: 8px;
}

.probe-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.status-badge {
  font-size: 13px;
  font-weight: 500;
}

.status-badge.success { color: var(--accent-success, #00e396); }
.status-badge.fail { color: var(--accent-danger, #ff4560); }

.structure-tag {
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 4px;
  color: var(--accent, #00d4ff);
  font-family: monospace;
}

.fields-title {
  font-size: 12px;
  color: var(--text-muted, #4a5578);
  margin-bottom: 6px;
}

.fields-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.field-tag {
  padding: 3px 10px;
  background: rgba(123, 97, 255, 0.12);
  border: 1px solid rgba(123, 97, 255, 0.25);
  border-radius: 4px;
  font-size: 12px;
  color: var(--accent-secondary, #7b61ff);
  font-family: monospace;
}

.field-tag.small {
  padding: 2px 6px;
  font-size: 11px;
}

.sample-json {
  background: var(--bg-primary, #0a0e27);
  padding: 10px;
  border-radius: 6px;
  font-size: 11px;
  color: var(--text-secondary, #8892b0);
  overflow-x: auto;
  max-height: 200px;
  margin: 0;
}

.probe-fail {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--accent-danger, #ff4560);
  font-size: 13px;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 16px;
}

.btn-save {
  padding: 8px 20px;
  background: linear-gradient(135deg, #7b61ff, #00d4ff);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.btn-save:disabled {
  opacity: 0.4;
  cursor: default;
}

.btn-cancel {
  padding: 8px 20px;
  background: transparent;
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 8px;
  color: var(--text-secondary, #8892b0);
  font-size: 14px;
  cursor: pointer;
}

/* 数据源列表 */
.ds-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
  margin-bottom: 16px;
}

.ds-card {
  padding: 14px 18px;
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 10px;
}

.ds-c.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.ds-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.ds-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #e0e6ff);
}

.ds-type {
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 4px;
  color: var(--accent, #00d4ff);
}

.ds-url {
  font-size: 12px;
  color: var(--text-muted, #4a5578);
  font-family: monospace;
  margin-bottom: 8px;
}

.ds-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 10px;
}

.field-more {
  font-size: 11px;
  color: var(--text-muted, #4a5578);
  padding: 2px 6px;
}

.ds-actions {
  display: flex;
  gap: 8px;
}

.btn-sm {
  padding: 4px 10px;
  font-size: 12px;
  background: var(--bg-tertiary, #1a2045);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 6px;
  color: var(--text-secondary, #8892b0);
  cursor: pointer;
}

.btn-sm.danger {
  border-color: var(--accent-danger, #ff4560);
  color: var(--accent-danger, #ff4560);
}

.add-more {
  text-align: center;
  padding: 16px 0;
}

.btn-add-more {
  padding: 8px 20px;
  background: var(--bg-tertiary, #1a2045);
  border: 1px dashed var(--border-color, #2a3560);
  border-radius: 8px;
  color: var(--text-secondary, #8892b0);
  font-size: 14px;
  cursor: pointer;
  margin-bottom: 10px;
}

.mock-hint {
  font-size: 12px;
  color: var(--text-muted, #4a5578);
}

.mock-link {
  color: var(--accent, #00d4ff);
  cursor: pointer;
  margin: 0 4px;
}

.mock-link:hover {
  text-decoration: underline;
}

/* Tab 切换 */
.source-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.tab-btn {
  padding: 8px 20px;
  border: 1px solid var(--border-color, #2a2d45);
  border-radius: 8px;
  background: transparent;
  color: var(--text-secondary, #8892b0);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.tab-btn.active {
  background: var(--accent, #00d4ff);
  color: #0a0e1a;
  border-color: var(--accent, #00d4ff);
  font-weight: 600;
}

.tab-btn:hover:not(.active) {
  border-color: var(--accent, #00d4ff);
  color: var(--accent, #00d4ff);
}

/* SQL 输入框 */
.sql-input {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  resize: vertical;
  min-height: 60px;
}

/* 数据库类型标签 */
.type-db {
  background: #7b61ff !important;
}

/* 数据源详情行 */
.ds-detail-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 12px;
}

.detail-label {
  flex-shrink: 0;
  padding: 1px 6px;
  background: rgba(0, 212, 255, 0.08);
  border-radius: 3px;
  color: var(--accent, #00d4ff);
  font-size: 11px;
  font-weight: 600;
}

.detail-value {
  color: var(--text-secondary, #8892b0);
  word-break: break-all;
}

.detail-value.mono {
  font-family: 'Courier New', monospace;
  font-size: 11px;
}

/* 描述 */
.ds-desc {
  font-size: 12px;
  color: var(--text-muted, #4a5578);
  margin-bottom: 8px;
  font-style: italic;
}

/* 字段区 */
.ds-fields-section {
  margin: 10px 0;
  padding: 10px;
  background: var(--bg-tertiary, #1a2045);
  border-radius: 8px;
}

.fields-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.fields-table {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.fields-table.editing {
  flex-direction: column;
  gap: 4px;
}

.field-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.field-annotation {
  font-size: 11px;
  color: var(--text-muted, #4a5578);
}

.annotation-input {
  flex: 1;
  padding: 3px 8px;
  background: var(--bg-primary, #0a0e27);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 4px;
  color: var(--text-primary, #e0e6ff);
  font-size: 12px;
  outline: none;
}

.annotation-input:focus {
  border-color: var(--accent, #00d4ff);
}

/* 数据库连接信息 */
.db-info-bar {
  display: flex;
  gap: 16px;
  padding: 8px 12px;
  background: rgba(123, 97, 255, 0.08);
  border: 1px solid rgba(123, 97, 255, 0.2);
  border-radius: 8px;
  margin-bottom: 14px;
  font-size: 12px;
}

.db-info-item {
  color: var(--text-secondary, #8892b0);
}

/* 代码输入框 */
.code-input {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  resize: vertical;
  min-height: 40px;
}

/* 提示文字 */
.hint {
  color: var(--text-muted, #4a5578);
  font-weight: normal;
}
</style>

