<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'
import { useDialog } from '../composables/useDialog'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const { confirm: showConfirm } = useDialog()

const projectId = computed(() => route.params.projectId)
const dashboards = computed(() => projectStore.getDashboards(projectId.value))

// 新建看板对话框
const showDialog = ref(false)
const newName = ref('新看板')
const newMode = ref('blank') // blank | ai
const aiPrompt = ref('')

function openDialog() {
  newName.value = '新看板'
  newMode.value = 'blank'
  aiPrompt.value = ''
  showDialog.value = true
}

function handleCreate() {
  if (!newName.value.trim()) return
  const db = projectStore.createDashboard(projectId.value, newName.value.trim())
  showDialog.value = false

  // 跳转到编辑器，如果选了 AI 模式，带上 prompt 参数
  const query = newMode.value === 'ai' && aiPrompt.value.trim()
    ? { aiPrompt: aiPrompt.value.trim() }
    : {}
  router.push({ name: 'dashboard-edit', params: { projectId: projectId.value, dashboardId: db.id }, query })
}

function openEditor(db) {
  router.push({ name: 'dashboard-edit', params: { projectId: projectId.value, dashboardId: db.id } })
}

async function handleDelete(db) {
  const ok = await showConfirm(`确定删除看板「${db.name}」？`)
  if (!ok) return
  projectStore.deleteDashboard(projectId.value, db.id)
}
</script>

<template>
  <div class="dashboard-list-page">
    <div class="page-header">
      <h1>看板列表</h1>
      <button class="btn-accent" @click="openDialog">＋ 新建看板</button>
    </div>

    <div class="card-grid" v-if="dashboards.length">
      <div v-for="db in dashboards" :key="db.id" class="db-card" @click="openEditor(db)">
        <div class="card-preview">
          <span class="card-icon">📊</span>
          <span class="widget-count">{{ (db.widgets || []).length }} 个组件</span>
        </div>
        <div class="card-info">
          <div class="card-title">{{ db.name }}</div>
          <div class="card-actions">
            <button class="btn-sm" @click.stop="handleDelete(db)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <div class="empty" v-else>
      <div class="empty-icon">📊</div>
      <p>还没有看板，创建你的第一个吧</p>
      <button class="btn-accent" @click="openDialog">开始创建</button>
    </div>

    <!-- 新建看板对话框 -->
    <div class="dialog-overlay" v-if="showDialog" @click.self="showDialog = false">
      <div class="dialog">
        <h2>新建看板</h2>
        <label class="field">
          <span>看板名称</span>
          <input v-model="newName" placeholder="输入看板名称" @keyup.enter="handleCreate" />
        </label>
        <div class="mode-group">
          <span class="mode-label">如何开始</span>
          <label class="mode-option" :class="{ active: newMode === 'blank' }">
            <input type="radio" v-model="newMode" value="blank" />
            <span class="mode-icon">🎨</span>
            <div>
              <div class="mode-title">空白画布</div>
              <div class="mode-desc">自己拖组件搭建</div>
            </div>
          </label>
          <label class="mode-option" :class="{ active: newMode === 'ai' }">
            <input type="radio" v-model="newMode" value="ai" />
            <span class="mode-icon">🤖</span>
            <div>
              <div class="mode-title">AI 生成</div>
              <div class="mode-desc">描述你想要的看板</div>
            </div>
          </label>
          <input
            v-if="newMode === 'ai'"
            v-model="aiPrompt"
            class="ai-input"
            placeholder="例如：做一个销售数据大屏"
          />
          <label class="mode-option disabled">
            <span class="mode-icon">📦</span>
            <div>
              <div class="mode-title">从模板选择</div>
              <div class="mode-desc">敬请期待</div>
            </div>
          </label>
        </div>
        <div class="dialog-actions">
          <button class="btn-ghost" @click="showDialog = false">取消</button>
          <button class="btn-accent" @click="handleCreate">创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-list-page { max-width: 960px; margin: 0 auto; }
.page-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 24px;
}
.page-header h1 { font-size: 24px; font-weight: 700; margin: 0; color: var(--text-primary, #e0e6ff); }

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}
.db-card {
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border, #2a3560);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.25s;
}
.db-card:hover { border-color: #00d4ff; transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,212,255,0.1); }
.card-preview {
  height: 90px;
  background: linear-gradient(135deg, rgba(0,212,255,0.06), rgba(123,97,255,0.06));
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px;
}
.card-icon { font-size: 28px; opacity: 0.5; }
.widget-count { font-size: 11px; color: var(--text-muted, #4a5578); }
.card-info { padding: 12px; display: flex; align-items: center; justify-content: space-between; }
.card-title { font-size: 14px; font-weight: 500; color: var(--text-primary, #e0e6ff); }
.btn-sm {
  font-size: 11px; padding: 3px 8px; border-radius: 4px; border: 1px solid var(--border, #2a3560);
  background: none; color: var(--text-muted, #4a5578); cursor: pointer; transition: all 0.2s;
}
.btn-sm:hover { border-color: #ff4560; color: #ff4560; }

/* 对话框 */
.dialog-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.dialog {
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border, #2a3560);
  border-radius: 16px;
  padding: 28px;
  width: 420px;
  max-width: 90vw;
}
.dialog h2 { font-size: 20px; font-weight: 700; margin: 0 0 20px; color: var(--text-primary, #e0e6ff); }

.field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px; }
.field span { font-size: 13px; color: var(--text-secondary, #8892b0); }
.field input {
  padding: 10px 12px; border-radius: 8px; border: 1px solid var(--border, #2a3560);
  background: var(--bg-primary, #0a0e27); color: var(--text-primary, #e0e6ff); font-size: 14px;
  outline: none; transition: border-color 0.2s;
}
.field input:focus { border-color: #00d4ff; }

.mode-group { margin-bottom: 20px; }
.mode-label { font-size: 13px; color: var(--text-secondary, #8892b0); display: block; margin-bottom: 8px; }
.mode-option {
  display: flex; align-items: center; gap: 12px; padding: 10px 12px; border-radius: 8px;
  border: 1px solid var(--border, #2a3560); margin-bottom: 8px; cursor: pointer; transition: all 0.2s;
}
.mode-option input[type="radio"] { display: none; }
.mode-option.active { border-color: #00d4ff; background: rgba(0,212,255,0.08); }
.mode-option.disabled { opacity: 0.4; cursor: not-allowed; }
.mode-icon { font-size: 24px; }
.mode-title { font-size: 14px; font-weight: 500; color: var(--text-primary, #e0e6ff); }
.mode-desc { font-size: 12px; color: var(--text-muted, #4a5578); }

.ai-input {
  width: 100%; padding: 8px 12px; border-radius: 8px; border: 1px solid var(--border, #2a3560);
  background: var(--bg-primary, #0a0e27); color: var(--text-primary, #e0e6ff); font-size: 13px;
  margin-bottom: 8px; outline: none; box-sizing: border-box;
}
.ai-input:focus { border-color: #00d4ff; }

.dialog-actions { display: flex; gap: 12px; justify-content: flex-end; }
.btn-accent {
  padding: 8px 20px; border-radius: 8px; border: none;
  background: linear-gradient(135deg, #7b61ff, #00d4ff); color: white; font-size: 13px;
  font-weight: 500; cursor: pointer; transition: opacity 0.2s;
}
.btn-accent:hover { opacity: 0.9; }
.btn-ghost {
  padding: 8px 20px; border-radius: 8px; border: 1px solid var(--border, #2a3560);
  background: none; color: var(--text-secondary, #8892b0); font-size: 13px; cursor: pointer;
}
.btn-ghost:hover { border-color: var(--text-secondary, #8892b0); }

.empty { text-align: center; padding: 80px 0; }
.empty-icon { font-size: 48px; margin-bottom: 16px; }
.empty p { color: var(--text-secondary, #8892b0); margin-bottom: 24px; }
</style>
