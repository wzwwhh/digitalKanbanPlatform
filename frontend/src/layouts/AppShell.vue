<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'
import { useThemeStore } from '../stores/theme'
import { useDialog } from '../composables/useDialog'
import SideNav from '../components/SideNav.vue'
import ThemePicker from '../components/ThemePicker.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const themeStore = useThemeStore()

const sideCollapsed = ref(false)
const currentProjectId = computed(() => route.params.projectId || null)

// 当路由中有 projectId 时，加载对应项目
watch(currentProjectId, (id) => {
  if (id) projectStore.loadProject(id)
}, { immediate: true })

const currentProject = computed(() => projectStore.currentProject)

function toggleSide() { sideCollapsed.value = !sideCollapsed.value }

const { prompt: showPrompt } = useDialog()

async function handleCreateProject() {
  const name = await showPrompt('新建项目', '新项目', '输入项目名称')
  if (!name) return
  const project = projectStore.createProject(name)
  router.push({ name: 'dashboards', params: { projectId: project.id } })
}
</script>

<template>
  <div class="app-shell">
    <!-- 顶栏 -->
    <header class="topbar">
      <div class="topbar-left">
        <button class="btn-toggle" @click="toggleSide" title="折叠导航">
          <span class="icon">☰</span>
        </button>
        <div class="logo" @click="router.push('/')">
          <span class="logo-icon">🎯</span>
          <span class="logo-text" v-show="!sideCollapsed">AI 看板平台</span>
        </div>
      </div>
      <div class="topbar-center">
        <nav class="breadcrumb">
          <router-link :to="{ name: 'workspace' }" class="crumb">🏠 工作台</router-link>
          <template v-if="currentProjectId">
            <span class="crumb-sep">/</span>
            <router-link :to="{ name: 'dashboards', params: { projectId: currentProjectId } }" class="crumb">
              {{ currentProject?.name || '项目' }}
            </router-link>
          </template>
          <template v-if="route.meta.title && route.name !== 'workspace' && route.name !== 'dashboards'">
            <span class="crumb-sep">/</span>
            <span class="crumb current">{{ route.meta.title }}</span>
          </template>
        </nav>
      </div>
      <div class="topbar-right">
        <ThemePicker
          :current-system-theme="themeStore.currentTheme"
          :show-board-style="false"
          @change-system="themeStore.applySystemTheme"
        />
        <button class="btn-primary" @click="handleCreateProject">
          ＋ 新建项目
        </button>
      </div>
    </header>

    <!-- 主体 -->
    <div class="shell-body">
      <SideNav
        :collapsed="sideCollapsed"
        :projectId="currentProjectId"
        :projectName="currentProject?.name"
      />
      <main class="shell-content">
        <router-view v-slot="{ Component }">
          <Transition name="fade" mode="out-in">
            <component :is="Component" />
          </Transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-primary, #0a0e27);
  color: var(--text-primary, #e0e6ff);
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* 顶栏 */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  padding: 0 16px;
  background: var(--bg-secondary, #131837);
  border-bottom: 1px solid var(--border, #2a3560);
  flex-shrink: 0;
  z-index: 100;
}
.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.topbar-center {
  flex: 1;
  display: flex;
  justify-content: center;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.btn-toggle {
  background: none;
  border: none;
  color: var(--text-secondary, #8892b0);
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s;
}
.btn-toggle:hover { background: rgba(255,255,255,0.08); }

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}
.logo-icon { font-size: 22px; }
.logo-text {
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #00d4ff, #7b61ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
}

.crumb {
  font-size: 13px;
  color: var(--text-secondary, #8892b0);
  text-decoration: none;
  padding: 3px 6px;
  border-radius: 4px;
  transition: all 0.15s;
}

.crumb:hover {
  color: var(--text-primary, #e0e6ff);
  background: rgba(255, 255, 255, 0.06);
}

.crumb.current {
  color: var(--text-primary, #e0e6ff);
  font-weight: 500;
}

.crumb-sep {
  color: var(--text-muted, #4a5578);
  font-size: 12px;
  user-select: none;
}

.btn-primary {
  padding: 6px 16px;
  border-radius: 8px;
  border: none;
  background: linear-gradient(135deg, #7b61ff, #00d4ff);
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s;
}
.btn-primary:hover { opacity: 0.9; }
.btn-primary:active { transform: scale(0.97); }

/* 主体 */
.shell-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}
.shell-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: var(--bg-primary, #0a0e27);
}

/* 页面内切换动画 */
.fade-enter-active { transition: opacity 0.15s ease; }
.fade-leave-active { transition: opacity 0.1s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
