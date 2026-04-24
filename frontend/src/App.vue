<template>
  <div class="app" :class="{ 'has-project': projectStore.hasProject }">
    <ProjectHome v-if="!projectStore.hasProject" />
    <DataSourceConfig
      v-else-if="showDsConfig"
      @done="showDsConfig = false"
    />
    <AppLayout v-else />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useProjectStore } from './stores/project'
import { useThemeStore } from './stores/theme'
import ProjectHome from './components/ProjectHome.vue'
import AppLayout from './components/AppLayout.vue'
import DataSourceConfig from './components/DataSourceConfig.vue'

const projectStore = useProjectStore()
const themeStore = useThemeStore()

const showDsConfig = ref(false)

// 当项目创建时，如果是 data-first 模式且无数据源，显示配置页
watch(() => projectStore.currentProject, (proj) => {
  if (proj && proj.mode === 'data-first' && (!proj.dataSources || proj.dataSources.length === 0)) {
    showDsConfig.value = true
  } else {
    showDsConfig.value = false
  }
})

onMounted(() => {
  projectStore.loadProjects()
  themeStore.initTheme()
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  /* 默认 dark-tech 变量（会被主题覆盖） */
  --bg-primary: #0a0e27;
  --bg-secondary: #131837;
  --bg-tertiary: #1a2045;
  --bg-card: #161d42;
  --border-color: #2a3560;
  --border-glow: rgba(0, 212, 255, 0.15);
  --accent: #00d4ff;
  --accent-secondary: #7b61ff;
  --accent-success: #00e396;
  --accent-warning: #feb019;
  --accent-danger: #ff4560;
  --text-primary: #e0e6ff;
  --text-secondary: #8892b0;
  --text-muted: #4a5578;
  --shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
  --shadow-glow: 0 0 20px rgba(0, 212, 255, 0.1);
  --font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

body {
  font-family: var(--font-family);
  background: var(--bg-primary);
  color: var(--text-primary);
  overflow: hidden;
  width: 100vw;
  height: 100vh;
}

#app {
  width: 100%;
  height: 100%;
}

.app {
  width: 100%;
  height: 100%;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--text-muted);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
}
</style>
