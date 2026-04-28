import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  // === 全局页面（AppShell 布局） ===
  {
    path: '/',
    component: () => import('../layouts/AppShell.vue'),
    children: [
      { path: '', name: 'workspace', component: () => import('../pages/WorkspacePage.vue'), meta: { title: '工作台' } },
      { path: 'projects', name: 'projects', component: () => import('../pages/ProjectListPage.vue'), meta: { title: '项目列表' } },

      // === 项目内页面 ===
      { path: 'project/:projectId/dashboards', name: 'dashboards', component: () => import('../pages/DashboardListPage.vue'), meta: { title: '看板列表' } },
      { path: 'project/:projectId/datasources', name: 'datasources', component: () => import('../pages/DataSourcePage.vue'), meta: { title: '数据源管理' } },
      { path: 'project/:projectId/ask', name: 'ask', component: () => import('../pages/AskPage.vue'), meta: { title: '智能问数' } },
      { path: 'project/:projectId/settings', name: 'settings', component: () => import('../pages/ProjectSettingsPage.vue'), meta: { title: '项目设置' } },
      { path: 'project/:projectId/materials', name: 'materials', component: () => import('../pages/MaterialLibPage.vue'), meta: { title: '素材库管理' } },

      // 项目概览重定向到看板列表
      { path: 'project/:projectId', redirect: to => ({ name: 'dashboards', params: { projectId: to.params.projectId } }) },
    ],
  },

  // === 看板编辑器（全屏，无 AppShell） ===
  {
    path: '/project/:projectId/dashboard/:dashboardId/edit',
    name: 'dashboard-edit',
    component: () => import('../pages/DashboardEditorPage.vue'),
    meta: { title: '编辑看板', fullscreen: true },
  },

  // === 看板预览（全屏，无边框） ===
  {
    path: '/project/:projectId/dashboard/:dashboardId/preview',
    name: 'dashboard-preview',
    component: () => import('../pages/DashboardPreviewPage.vue'),
    meta: { title: '预览看板', fullscreen: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 动态页面标题
router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} - AI看板平台` : 'AI看板平台'
})

export default router
