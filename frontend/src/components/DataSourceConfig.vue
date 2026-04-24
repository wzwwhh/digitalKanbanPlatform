<template>
  <div class="ds-config">
    <div class="ds-header">
      <h3 class="ds-title">数据源配置</h3>
      <p class="ds-desc">配置 API 或数据库，AI 将基于真实数据生成看板</p>
    </div>

    <!-- 添加新数据源 -->
    <div class="ds-add">
      <div class="ds-type-tabs">
        <button class="type-tab" :class="{ active: addType === 'api' }" @click="addType = 'api'">🔗 API</button>
        <button class="type-tab" :class="{ active: addType === 'db' }" @click="addType = 'db'">🗄️ 数据库</button>
      </div>

      <!-- API 配置 -->
      <div v-if="addType === 'api'" class="ds-form">
        <label class="form-label">API 地址</label>
        <input v-model="apiUrl" class="form-input" placeholder="https://api.example.com/data" />
        <label class="form-label">请求方式</label>
        <select v-model="apiMethod" class="form-input">
          <option>GET</option>
          <option>POST</option>
        </select>
        <button class="btn-probe" @click="probeApi" :disabled="probing || !apiUrl.trim()">
          {{ probing ? '⏳ 探测中...' : '🔍 探测字段' }}
        </button>
      </div>

      <!-- DB 配置 -->
      <div v-if="addType === 'db'" class="ds-form">
        <p class="form-hint">🚧 数据库连接功能开发中</p>
      </div>
    </div>

    <!-- 探测结果 -->
    <div v-if="probeResult" class="probe-result" :class="{ error: probeResult.status !== 200 }">
      <div class="probe-status">
        {{ probeResult.status === 200 ? '✅ 探测成功' : '❌ 探测失败' }}
        <span class="probe-structure">结构: {{ probeResult.structure }}</span>
      </div>

      <div v-if="probeResult.fields.length > 0" class="probe-fields">
        <div class="field-label">字段列表 ({{ probeResult.fields.length }})</div>
        <div class="field-tags">
          <span v-for="f in probeResult.fields" :key="f" class="field-tag">{{ f }}</span>
        </div>
      </div>

      <button
        v-if="probeResult.status === 200"
        class="btn-add-ds"
        @click="addDataSource"
      >
        ➕ 添加到数据源
      </button>
    </div>

    <!-- 已有数据源 -->
    <div class="ds-list" v-if="projectStore.currentProject?.dataSources?.length > 0">
      <div class="ds-list-title">已添加的数据源</div>
      <div
        v-for="ds in projectStore.currentProject.dataSources"
        :key="ds.id"
        class="ds-item"
      >
        <div class="ds-item-info">
          <span class="ds-item-icon">{{ ds.type === 'api' ? '🔗' : '🗄️' }}</span>
          <span class="ds-item-name">{{ ds.name }}</span>
          <span class="ds-item-fields">{{ ds.fields?.length || 0 }} 字段</span>
        </div>
        <button class="ds-item-remove" @click="removeDs(ds.id)">✕</button>
      </div>
    </div>

    <!-- 完成按钮 -->
    <div v-if="projectStore.currentProject?.dataSources?.length > 0" class="ds-done">
      <button class="btn-done" @click="$emit('done')">
        🚀 开始设计看板
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useProjectStore } from '../stores/project'

const projectStore = useProjectStore()

const emit = defineEmits(['done'])

const addType = ref('api')
const apiUrl = ref('')
const apiMethod = ref('GET')
const probing = ref(false)
const probeResult = ref(null)

async function probeApi() {
  if (!apiUrl.value.trim()) return
  probing.value = true
  probeResult.value = null

  try {
    const response = await fetch('/api/data/probe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: apiUrl.value.trim(),
        method: apiMethod.value,
      }),
    })
    probeResult.value = await response.json()
  } catch (err) {
    probeResult.value = { status: -1, fields: [], sample: [], structure: `请求失败: ${err.message}` }
  } finally {
    probing.value = false
  }
}

function addDataSource() {
  if (!probeResult.value) return

  const ds = {
    type: 'api',
    name: new URL(apiUrl.value).pathname.split('/').filter(Boolean).pop() || 'API数据源',
    url: apiUrl.value,
    method: apiMethod.value,
    fields: probeResult.value.fields,
    sample: probeResult.value.sample,
    structure: probeResult.value.structure,
  }

  projectStore.addDataSource(ds)

  // 清空表单
  apiUrl.value = ''
  probeResult.value = null
}

function removeDs(dsId) {
  projectStore.removeDataSource(dsId)
}
</script>

<style scoped>
.ds-config {
  padding: 24px;
  max-width: 600px;
  margin: 0 auto;
}

.ds-header {
  margin-bottom: 24px;
}

.ds-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.ds-desc {
  font-size: 13px;
  color: var(--text-secondary);
}

.ds-type-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.type-tab {
  flex: 1;
  padding: 10px;
  border: 1px solid var(--border-color);
  background: var(--bg-tertiary);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.type-tab.active {
  border-color: var(--accent);
  color: var(--accent);
  background: rgba(0, 212, 255, 0.05);
}

.ds-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.form-input {
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
  font-family: inherit;
}

.form-input:focus {
  border-color: var(--accent);
}

.form-hint {
  font-size: 13px;
  color: var(--text-muted);
  text-align: center;
  padding: 20px;
}

.btn-probe {
  padding: 10px;
  background: var(--accent);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  margin-top: 4px;
}

.btn-probe:hover:not(:disabled) {
  opacity: 0.85;
}

.btn-probe:disabled {
  opacity: 0.4;
}

/* 探测结果 */
.probe-result {
  margin-top: 16px;
  padding: 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--accent-success);
  border-radius: 8px;
}

.probe-result.error {
  border-color: var(--accent-danger);
}

.probe-status {
  font-size: 14px;
  margin-bottom: 8px;
}

.probe-structure {
  font-size: 12px;
  color: var(--text-muted);
  margin-left: 8px;
}

.probe-fields {
  margin-top: 8px;
}

.field-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.field-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.field-tag {
  padding: 2px 8px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 12px;
  color: var(--text-secondary);
  font-family: monospace;
}

.btn-add-ds {
  margin-top: 12px;
  width: 100%;
  padding: 10px;
  background: var(--accent-success);
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
}

/* 数据源列表 */
.ds-list {
  margin-top: 24px;
}

.ds-list-title {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.ds-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  margin-bottom: 6px;
}

.ds-item-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ds-item-name {
  font-size: 13px;
  color: var(--text-primary);
}

.ds-item-fields {
  font-size: 11px;
  color: var(--text-muted);
}

.ds-item-remove {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 14px;
}

.ds-item-remove:hover {
  color: var(--accent-danger);
}

.ds-done {
  margin-top: 24px;
}

.btn-done {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, var(--accent), var(--accent-secondary));
  border: none;
  border-radius: 10px;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-done:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 20px rgba(0, 212, 255, 0.3);
}
</style>
