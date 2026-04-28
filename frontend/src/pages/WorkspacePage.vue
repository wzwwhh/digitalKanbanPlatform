<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'
import { useDialog } from '../composables/useDialog'

const router = useRouter()
const projectStore = useProjectStore()
const { prompt: showPrompt } = useDialog()

// 统计
const stats = computed(() => {
  const projs = projectStore.projects
  let dbCount = 0, dsCount = 0
  for (const p of projs) {
    dbCount += (p.dashboards || []).length
    dsCount += (p.dataSources || []).length
  }
  return { projects: projs.length, dashboards: dbCount, dataSources: dsCount }
})

// 最近编辑的看板（跨项目，按最后编辑/创建时间排序）
const recentDashboards = computed(() => {
  const all = []
  for (const proj of projectStore.projects) {
    for (const db of proj.dashboards || []) {
      all.push({
        ...db,
        projectId: proj.id,
        projectName: proj.name,
        sortTime: db.savedAt || db.createdAt || '',
        widgetCount: (db.widgets || []).length,
      })
    }
  }
  return all.sort((a, b) => b.sortTime.localeCompare(a.sortTime)).slice(0, 8)
})

function openDashboard(item) {
  router.push({ name: 'dashboard-edit', params: { projectId: item.projectId, dashboardId: item.id } })
}

function goProjects() { router.push({ name: 'projects' }) }

async function handleCreateProject() {
  const name = await showPrompt('新建项目', '新项目', '输入项目名称')
  if (!name) return
  const project = projectStore.createProject(name)
  router.push({ name: 'dashboards', params: { projectId: project.id } })
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return d.toLocaleDateString('zh-CN')
}
</script>

<template>
  <div class="workspace-page">
    <!-- 欢迎区 -->
    <section class="welcome">
      <div class="welcome-icon">🎯</div>
      <h1>欢迎回来</h1>
      <p class="welcome-sub">连上数据，说句话，导出来直接部署</p>
      <div class="welcome-actions">
        <button class="btn-accent" @click="handleCreateProject">＋ 新建项目</button>
        <button class="btn-ghost" @click="goProjects">📁 所有项目</button>
      </div>
    </section>

    <!-- 统计概览 -->
    <section class="stats-bar" v-if="stats.projects > 0">
      <div class="stat-item">
        <span class="stat-num">{{ stats.projects }}</span>
        <span class="stat-label">项目</span>
      </div>
      <div class="stat-item">
        <span class="stat-num">{{ stats.dashboards }}</span>
        <span class="stat-label">看板</span>
      </div>
      <div class="stat-item">
        <span class="stat-num">{{ stats.dataSources }}</span>
        <span class="stat-label">数据源</span>
      </div>
    </section>

    <!-- 新手引导 -->
    <section class="onboarding">
      <h2>🚀 三步开始</h2>
      <div class="steps">
        <div class="step">
          <span class="step-num">1</span>
          <div class="step-body">
            <strong>新建项目</strong>
            <p>点击上方「新建项目」创建你的第一个项目</p>
          </div>
        </div>
        <div class="step">
          <span class="step-num">2</span>
          <div class="step-body">
            <strong>连接数据</strong>
            <p>添加 API 数据源，或使用内置模拟数据快速体验</p>
          </div>
        </div>
        <div class="step">
          <span class="step-num">3</span>
          <div class="step-body">
            <strong>AI 生成看板</strong>
            <p>对 AI 说"做一个销售看板"，自动生成完整布局</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 最近看板 -->
    <section class="recent" v-if="recentDashboards.length">
      <h2>最近看板</h2>
      <div class="card-grid">
        <div
          v-for="item in recentDashboards"
          :key="item.id"
          class="dashboard-card"
          @click="openDashboard(item)"
        >
          <div class="card-preview">
            <span class="card-icon">{{ item.widgetCount > 0 ? '📊' : '📝' }}</span>
            <span class="card-widget-count" v-if="item.widgetCount">{{ item.widgetCount }} 组件</span>
          </div>
          <div class="card-info">
            <div class="card-title">{{ item.name }}</div>
            <div class="card-meta">
              <span>{{ item.projectName }}</span>
              <span v-if="item.sortTime" class="card-time">{{ formatTime(item.sortTime) }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 空状态 -->
    <section class="empty" v-if="!recentDashboards.length">
      <div class="empty-icon">🚀</div>
      <p>还没有看板，创建你的第一个项目吧</p>
      <button class="btn-accent" @click="handleCreateProject">开始创建</button>
    </section>
  </div>
</template>

<style scoped>
.workspace-page {
  max-width: 960px;
  margin: 0 auto;
}

/* 欢迎区 */
.welcome {
  text-align: center;
  padding: 48px 0 32px;
}
.welcome-icon { font-size: 48px; margin-bottom: 12px; }
.welcome h1 {
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #00d4ff, #7b61ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0 0 8px;
}
.welcome-sub {
  color: var(--text-secondary, #8892b0);
  font-size: 15px;
  margin-bottom: 24px;
}
.welcome-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

/* 按钮 */
.btn-accent {
  padding: 10px 24px;
  border-radius: 10px;
  border: none;
  background: linear-gradient(135deg, #7b61ff, #00d4ff);
  color: white;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s;
}
.btn-accent:hover { opacity: 0.9; }
.btn-accent:active { transform: scale(0.97); }

.btn-ghost {
  padding: 10px 24px;
  border-radius: 10px;
  border: 1px solid var(--border, #2a3560);
  background: transparent;
  color: var(--text-secondary, #8892b0);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-ghost:hover {
  border-color: #00d4ff;
  color: #00d4ff;
}

/* 最近编辑 */
.recent h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 16px;
  color: var(--text-primary, #e0e6ff);
}

/* 新手引导 */
.onboarding {
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border-color, #2a3560);
  border-radius: 16px;
  padding: 24px 32px;
  margin-bottom: 24px;
}
.onboarding h2 {
  font-size: 18px;
  color: var(--text-primary, #e0e6ff);
  margin: 0 0 16px;
}
.steps {
  display: flex;
  gap: 24px;
}
.step {
  flex: 1;
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 16px;
  background: var(--bg-tertiary, #1a2045);
  border-radius: 12px;
  border: 1px solid var(--border-color, #2a3560);
}
.step-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #7b61ff, #00d4ff);
  color: white;
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.step-body strong {
  color: var(--text-primary, #e0e6ff);
  font-size: 14px;
}
.step-body p {
  color: var(--text-secondary, #8892b0);
  font-size: 12px;
  margin: 4px 0 0;
  line-height: 1.4;
}
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}
.dashboard-card {
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border, #2a3560);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.25s;
}
.dashboard-card:hover {
  border-color: #00d4ff;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 212, 255, 0.1);
}
.card-icon { font-size: 32px; opacity: 0.6; }
.card-info { padding: 12px; }
.card-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #e0e6ff);
  margin-bottom: 4px;
}
.card-meta {
  font-size: 12px;
  color: var(--text-muted, #4a5578);
  display: flex;
  justify-content: space-between;
}

.card-time {
  color: var(--text-muted, #4a5578);
}

.card-widget-count {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(0, 212, 255, 0.12);
  color: #00d4ff;
}

.card-preview {
  height: 100px;
  background: linear-gradient(135deg, rgba(0,212,255,0.05), rgba(123,97,255,0.05));
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

/* 统计栏 */
.stats-bar {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-bottom: 32px;
}

.stat-item {
  text-align: center;
  padding: 16px 32px;
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border, #2a3560);
  border-radius: 10px;
  min-width: 100px;
}

.stat-num {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: #00d4ff;
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted, #4a5578);
  margin-top: 2px;
}

/* 空状态 */
.empty {
  text-align: center;
  padding: 80px 0;
}
.empty-icon { font-size: 48px; margin-bottom: 16px; }
.empty p {
  color: var(--text-secondary, #8892b0);
  margin-bottom: 24px;
}
</style>
