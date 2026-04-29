<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'

const props = defineProps({
  collapsed: { type: Boolean, default: false },
  projectId: { type: String, default: null },
  projectName: { type: String, default: null },
})

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

// 项目内导航菜单
const projectMenus = computed(() => {
  if (!props.projectId) return []
  const proj = projectStore?.projects?.find(p => p.id === props.projectId)
  const dbCount = (proj?.dashboards || []).length
  const dsCount = (proj?.dataSources || []).length
  return [
    { key: 'dashboards', icon: '📊', label: '看板', badge: dbCount || null, to: { name: 'dashboards', params: { projectId: props.projectId } } },
    { key: 'datasources', icon: '🔗', label: '数据源', badge: dsCount || null, to: { name: 'datasources', params: { projectId: props.projectId } } },
    { key: 'materials', icon: '🧩', label: '素材库', to: { name: 'materials', params: { projectId: props.projectId } } },
    { key: 'ask', icon: '🤖', label: '智能问数', to: { name: 'ask', params: { projectId: props.projectId } } },
    { key: 'settings', icon: '⚙️', label: '设置', to: { name: 'settings', params: { projectId: props.projectId } } },
  ]
})

// 全局导航菜单
const globalMenus = [
  { key: 'workspace', icon: '🏠', label: '工作台', to: { name: 'workspace' } },
  { key: 'projects', icon: '📁', label: '项目', to: { name: 'projects' } },
]

function isActive(menu) {
  return route.name === menu.key
}
</script>

<template>
  <nav class="side-nav" :class="{ collapsed }">
    <!-- 项目菜单 -->
    <template v-if="projectId">
      <div class="nav-section-title" v-show="!collapsed">
        <span class="section-dot"></span>
        {{ projectName || '当前项目' }}
      </div>
      <router-link
        v-for="menu in projectMenus"
        :key="menu.key"
        :to="menu.to"
        class="nav-item"
        :class="{ active: isActive(menu) }"
        :title="collapsed ? menu.label : ''"
      >
        <span class="nav-icon">{{ menu.icon }}</span>
        <span class="nav-label" v-show="!collapsed">{{ menu.label }}</span>
        <span v-if="menu.badge && !collapsed" class="nav-badge">{{ menu.badge }}</span>
      </router-link>
      <div class="nav-divider"></div>
    </template>

    <!-- 全局菜单 -->
    <div class="nav-section-title" v-show="!collapsed">
      <span class="section-dot global"></span>
      全局
    </div>
    <router-link
      v-for="menu in globalMenus"
      :key="menu.key"
      :to="menu.to"
      class="nav-item"
      :class="{ active: isActive(menu) }"
      :title="collapsed ? menu.label : ''"
    >
      <span class="nav-icon">{{ menu.icon }}</span>
      <span class="nav-label" v-show="!collapsed">{{ menu.label }}</span>
    </router-link>
  </nav>
</template>

<style scoped>
.side-nav {
  width: 200px;
  background: var(--bg-secondary, #131837);
  border-right: 1px solid var(--border, #2a3560);
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex-shrink: 0;
  transition: width 0.25s ease;
  overflow: hidden;
}
.side-nav.collapsed {
  width: 56px;
}

.nav-section-title {
  font-size: 11px;
  color: var(--text-muted, #4a5578);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 12px 12px 6px;
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}
.section-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #00d4ff;
  flex-shrink: 0;
}
.section-dot.global { background: #7b61ff; }

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  color: var(--text-secondary, #8892b0);
  text-decoration: none;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.nav-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-primary, #e0e6ff);
}
.nav-item.active {
  background: rgba(0, 212, 255, 0.12);
  color: #00d4ff;
}

.nav-icon {
  font-size: 18px;
  flex-shrink: 0;
  width: 24px;
  text-align: center;
}
.nav-label {
  flex: 1;
}

.nav-divider {
  height: 1px;
  background: var(--border, #2a3560);
  margin: 8px 12px;
}

.nav-badge {
  font-size: 11px;
  padding: 1px 7px;
  border-radius: 10px;
  background: rgba(0, 212, 255, 0.12);
  color: #00d4ff;
  font-weight: 500;
}
</style>
