<template>
  <div class="project-home">
    <div class="home-container">
      <!-- Logo 区域 -->
      <div class="logo-area">
        <div class="logo-icon">🎯</div>
        <h1 class="logo-title">AI 看板平台</h1>
        <p class="logo-subtitle">连上数据，说句话，导出来直接部署</p>
      </div>

      <!-- 新建项目 -->
      <div class="action-cards">
        <div class="action-card primary" @click="createDataFirst">
          <div class="card-icon">🔗</div>
          <div class="card-title">从数据开始</div>
          <div class="card-desc">推荐 · 先配置数据源，AI 基于真实数据设计看板</div>
        </div>
        <div class="action-card" @click="createDesignFirst">
          <div class="card-icon">🎨</div>
          <div class="card-title">从模板开始</div>
          <div class="card-desc">先设计布局，后续再连接数据</div>
        </div>
      </div>

      <!-- 已有项目 -->
      <div v-if="projectStore.projects.length > 0" class="recent-projects">
        <h3 class="section-title">已有项目</h3>
        <div class="project-list">
          <div
            v-for="project in projectStore.projects"
            :key="project.id"
            class="project-item"
            @click="openProject(project.id)"
          >
            <span class="project-icon">📊</span>
            <div class="project-info">
              <div class="project-name">{{ project.name }}</div>
              <div class="project-date">{{ formatDate(project.savedAt) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useProjectStore } from '../stores/project'
import { useDashboardStore } from '../stores/dashboard'

const projectStore = useProjectStore()
const dashboardStore = useDashboardStore()

function createDataFirst() {
  const name = prompt('输入项目名称:', '我的看板') || '我的看板'
  projectStore.createProject(name, 'data-first')
  // TODO: 跳转到数据源配置页（暂时直接进入工作区）
}

function createDesignFirst() {
  const name = prompt('输入项目名称:', '我的看板') || '我的看板'
  projectStore.createProject(name, 'design-first')
}

function openProject(projectId) {
  const widgets = projectStore.openProject(projectId)
  dashboardStore.setWidgets(widgets)
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.project-home {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
}

.home-container {
  max-width: 640px;
  width: 100%;
  padding: 40px;
}

.logo-area {
  text-align: center;
  margin-bottom: 48px;
}

.logo-icon {
  font-size: 56px;
  margin-bottom: 16px;
  filter: drop-shadow(0 0 20px rgba(0, 212, 255, 0.4));
}

.logo-title {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.logo-subtitle {
  font-size: 16px;
  color: var(--text-secondary);
}

.action-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 48px;
}

.action-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-card:hover {
  border-color: var(--accent);
  box-shadow: var(--shadow-glow);
  transform: translateY(-2px);
}

.action-card.primary {
  border-color: var(--accent);
  background: linear-gradient(135deg, var(--bg-secondary), rgba(0, 212, 255, 0.05));
}

.card-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.card-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.section-title {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.project-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.project-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.project-item:hover {
  border-color: var(--accent);
  background: var(--bg-tertiary);
}

.project-icon {
  font-size: 20px;
}

.project-name {
  font-size: 15px;
  color: var(--text-primary);
  font-weight: 500;
}

.project-date {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}
</style>
