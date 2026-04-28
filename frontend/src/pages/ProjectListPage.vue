<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'
import { useDialog } from '../composables/useDialog'

const router = useRouter()
const projectStore = useProjectStore()
const { prompt: showPrompt, confirm: showConfirm } = useDialog()

const projects = computed(() => projectStore.projects)

function openProject(project) {
  router.push({ name: 'dashboards', params: { projectId: project.id } })
}

async function handleCreate() {
  const name = await showPrompt('新建项目', '新项目', '输入项目名称')
  if (!name) return
  const project = projectStore.createProject(name)
  router.push({ name: 'dashboards', params: { projectId: project.id } })
}

async function handleDelete(project) {
  const ok = await showConfirm(`确定删除项目「${project.name}」？该操作不可撤销。`)
  if (!ok) return
  projectStore.deleteProject(project.id)
}
</script>

<template>
  <div class="project-list-page">
    <div class="page-header">
      <h1>所有项目</h1>
      <button class="btn-accent" @click="handleCreate">＋ 新建项目</button>
    </div>

    <div class="project-grid" v-if="projects.length">
      <div
        v-for="proj in projects"
        :key="proj.id"
        class="project-card"
        @click="openProject(proj)"
      >
        <div class="card-top">
          <span class="card-emoji">📂</span>
          <button class="btn-delete" @click.stop="handleDelete(proj)" title="删除">✕</button>
        </div>
        <div class="card-body">
          <div class="card-name">{{ proj.name }}</div>
          <div class="card-stats">
            <span>📊 {{ (proj.dashboards || []).length }} 个看板</span>
            <span>🔗 {{ (proj.dataSources || []).length }} 个数据源</span>
          </div>
        </div>
      </div>
    </div>

    <div class="empty" v-else>
      <div class="empty-icon">📂</div>
      <p>暂无项目</p>
      <button class="btn-accent" @click="handleCreate">创建第一个项目</button>
    </div>
  </div>
</template>

<style scoped>
.project-list-page { max-width: 960px; margin: 0 auto; }
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}
.page-header h1 {
  font-size: 24px;
  font-weight: 700;
  margin: 0;
  color: var(--text-primary, #e0e6ff);
}
.btn-accent {
  padding: 8px 20px;
  border-radius: 8px;
  border: none;
  background: linear-gradient(135deg, #7b61ff, #00d4ff);
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}
.btn-accent:hover { opacity: 0.9; }

.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}
.project-card {
  background: var(--bg-secondary, #131837);
  border: 1px solid var(--border, #2a3560);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.25s;
}
.project-card:hover {
  border-color: #7b61ff;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(123, 97, 255, 0.12);
}
.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.card-emoji { font-size: 28px; }
.btn-delete {
  background: none;
  border: none;
  color: var(--text-muted, #4a5578);
  font-size: 14px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
}
.btn-delete:hover { color: #ff4560; background: rgba(255,69,96,0.1); }

.card-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #e0e6ff);
  margin-bottom: 8px;
}
.card-stats {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-muted, #4a5578);
}

.empty {
  text-align: center;
  padding: 80px 0;
}
.empty-icon { font-size: 48px; margin-bottom: 16px; }
.empty p { color: var(--text-secondary, #8892b0); margin-bottom: 24px; }
</style>
