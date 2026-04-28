<script setup>
/**
 * 预览页面 — 全屏无边框看板展示
 *
 * 特性:
 * - 复用 WidgetWrapper 渲染所有组件
 * - ESC 键返回编辑器
 * - 自适应缩放到窗口大小
 * - 底部浮动返回按钮
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'
import { useThemeStore } from '../stores/theme'
import '../widgets/_registry.js'

// 动态导入 WidgetWrapper（它内部会通过 registry 加载具体组件）
import WidgetWrapper from '../widgets/WidgetWrapper.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const themeStore = useThemeStore()

const projectId = computed(() => route.params.projectId)
const dashboardId = computed(() => route.params.dashboardId)

const widgets = ref([])
const dashboardName = ref('')
const canvasW = 1920
const canvasH = 1080
const scale = ref(1)
const isFullscreen = ref(false)

function calcScale() {
  scale.value = Math.min(
    window.innerWidth / canvasW,
    window.innerHeight / canvasH,
  )
}

function goBack() {
  if (projectId.value && dashboardId.value) {
    router.push({
      name: 'dashboard-edit',
      params: { projectId: projectId.value, dashboardId: dashboardId.value },
    })
  } else {
    router.back()
  }
}

function toggleFullscreen() {
  if (document.fullscreenElement) {
    document.exitFullscreen()
    isFullscreen.value = false
  } else {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  }
}

function onKeyDown(e) {
  // 忽略输入框内按键
  const tag = e.target.tagName.toLowerCase()
  if (tag === 'input' || tag === 'textarea' || tag === 'select') return

  if (e.key === 'Escape') {
    if (isFullscreen.value) {
      document.exitFullscreen()
      isFullscreen.value = false
    } else {
      goBack()
    }
  }
  if (e.key === 'f' || e.key === 'F') {
    toggleFullscreen()
  }
}

onMounted(() => {
  // 加载项目 + 看板数据
  if (projectId.value) {
    projectStore.loadProject(projectId.value)
    if (dashboardId.value) {
      const db = projectStore.getDashboard(projectId.value, dashboardId.value)
      widgets.value = db?.widgets || []
      dashboardName.value = db?.name || '预览'
    }
  }

  themeStore.initTheme()
  calcScale()
  window.addEventListener('resize', calcScale)
  document.addEventListener('keydown', onKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('resize', calcScale)
  document.removeEventListener('keydown', onKeyDown)
})

const canvasStyle = computed(() => ({
  width: `${canvasW}px`,
  height: `${canvasH}px`,
  transform: `scale(${scale.value})`,
}))
</script>

<template>
  <div class="preview-page">
    <div class="preview-canvas" :style="canvasStyle">
      <WidgetWrapper
        v-for="w in widgets"
        :key="w.id"
        :widget="w"
        :selected="false"
      />
    </div>
    <!-- 浮动操作栏 -->
    <div class="preview-controls">
      <button class="preview-back" @click="goBack">← 返回编辑器</button>
      <span class="preview-name">{{ dashboardName }}</span>
      <span class="preview-count">{{ widgets.length }} 组件</span>
      <button class="preview-btn" @click="toggleFullscreen">{{ isFullscreen ? '⬜ 退出全屏' : '⛶ 全屏' }}</button>
      <span class="preview-hint">ESC 返回 · F 全屏</span>
    </div>
  </div>
</template>

<style scoped>
.preview-page {
  width: 100vw;
  height: 100vh;
  background: var(--bg-primary);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.preview-canvas {
  position: relative;
  transform-origin: center center;
  flex-shrink: 0;
}

.preview-controls {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(10px);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 100;
  opacity: 0.4;
  transition: opacity 0.3s;
}

.preview-controls:hover {
  opacity: 1;
}

.preview-back {
  padding: 6px 14px;
  border: 1px solid var(--accent);
  background: transparent;
  color: var(--accent);
  border-radius: 16px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.preview-back:hover {
  background: var(--accent);
  color: #fff;
}

.preview-hint {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
}

.preview-name {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
}

.preview-count {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(0, 212, 255, 0.15);
  color: #00d4ff;
}

.preview-btn {
  padding: 4px 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: transparent;
  color: rgba(255, 255, 255, 0.7);
  border-radius: 12px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.preview-btn:hover {
  border-color: var(--accent, #00d4ff);
  color: var(--accent, #00d4ff);
}
</style>
