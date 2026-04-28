<template>
  <router-view v-slot="{ Component }">
    <Transition name="page" mode="out-in">
      <component :is="Component" />
    </Transition>
  </router-view>
  <GlobalDialog />
</template>

<script setup>
import GlobalDialog from './components/GlobalDialog.vue'
</script>

<style>
/* 全局基础样式 */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  color-scheme: dark;
  --bg-primary: #0a0e27;
  --bg-secondary: #131837;
  --bg-card: #161d42;
  --border: #2a3560;
  --accent: #00d4ff;
  --accent-purple: #7b61ff;
  --text-primary: #e0e6ff;
  --text-secondary: #8892b0;
  --text-muted: #4a5578;
  --danger: #ff4560;
  --success: #00e396;
}

body {
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  width: 100%;
  height: 100vh;
}

/* 全局滚动条美化 */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* 页面切换动画 */
.page-enter-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.page-leave-active { transition: opacity 0.1s ease; }
.page-enter-from { opacity: 0; transform: translateY(6px); }
.page-leave-to { opacity: 0; }

/* 修复下拉框选项的背景色 */
select option {
  background: var(--bg-secondary);
  color: var(--text-primary);
}
</style>
