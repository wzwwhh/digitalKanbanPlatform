/**
 * Project Store - 项目 + 看板管理（支持 1:N 关系）
 *
 * 数据结构:
 *   Project = { id, name, theme, dataSources[], dashboards[] }
 *   Dashboard = { id, name, widgets[], boardTheme, createdAt, savedAt }
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { nanoid } from 'nanoid'
import { persistence } from '../services/persistence'

export const useProjectStore = defineStore('project', () => {
  // 所有项目列表
  const projects = ref([])
  // 当前打开的项目
  const currentProject = ref(null)

  const hasProject = computed(() => currentProject.value !== null)

  // ========== 项目 CRUD ==========

  function createProject(name) {
    const project = {
      id: `proj_${nanoid(10)}`,
      name,
      theme: 'dark-tech',
      dataSources: [],
      dashboards: [],
      createdAt: new Date().toISOString(),
    }
    projects.value.push(project)
    currentProject.value = project
    _persist()
    return project
  }

  function deleteProject(projectId) {
    projects.value = projects.value.filter(p => p.id !== projectId)
    if (currentProject.value?.id === projectId) {
      currentProject.value = null
    }
    _persist()
  }

  function loadProject(projectId) {
    const project = projects.value.find(p => p.id === projectId)
    if (project) {
      currentProject.value = _normalize(project)
    }
    return currentProject.value
  }

  // ========== 看板 CRUD ==========

  function getDashboards(projectId) {
    const proj = projects.value.find(p => p.id === projectId)
    return proj?.dashboards || []
  }

  function createDashboard(projectId, name) {
    const proj = projects.value.find(p => p.id === projectId)
    if (!proj) return null
    const dashboard = {
      id: `db_${nanoid(10)}`,
      name,
      widgets: [],
      boardTheme: null,  // null = 跟随系统主题
      bgImage: null,     // 大屏背景图URL
      createdAt: new Date().toISOString(),
      savedAt: null,
    }
    if (!proj.dashboards) proj.dashboards = []
    proj.dashboards.push(dashboard)
    _persist()
    return dashboard
  }

  function deleteDashboard(projectId, dashboardId) {
    const proj = projects.value.find(p => p.id === projectId)
    if (!proj) return
    proj.dashboards = (proj.dashboards || []).filter(d => d.id !== dashboardId)
    _persist()
  }

  function getDashboard(projectId, dashboardId) {
    const proj = projects.value.find(p => p.id === projectId)
    if (!proj) return null
    return (proj.dashboards || []).find(d => d.id === dashboardId) || null
  }

  function saveDashboard(projectId, dashboardId, widgets, boardTheme, bgImage) {
    const db = getDashboard(projectId, dashboardId)
    if (!db) return
    
    // Deep clone to prevent proxy entanglement and circular references
    try {
      db.widgets = JSON.parse(JSON.stringify(widgets || []))
    } catch (e) {
      console.error('[projectStore] saveDashboard failed to stringify widgets:', e)
      db.widgets = []
    }
    
    if (boardTheme !== undefined) {
      db.boardTheme = boardTheme
    }
    if (bgImage !== undefined) {
      db.bgImage = bgImage
    }
    db.savedAt = new Date().toISOString()
    _persist()
  }

  // ========== 数据源管理 ==========

  function addDataSource(ds) {
    if (!currentProject.value) return null
    const dataSource = { id: `ds_${nanoid(8)}`, ...ds }
    currentProject.value.dataSources.push(dataSource)
    _persist()
    return dataSource
  }

  function removeDataSource(dsId) {
    if (!currentProject.value) return
    currentProject.value.dataSources = currentProject.value.dataSources.filter(
      ds => ds.id !== dsId
    )
    _persist()
  }

  function updateDataSource(dsId, patch) {
    if (!currentProject.value) return
    const ds = currentProject.value.dataSources.find(d => d.id === dsId)
    if (ds) {
      Object.assign(ds, patch)
      _persist()
    }
  }

  // ========== 兼容旧版 saveProject ==========

  function copyDataSources(fromProjectId) {
    if (!currentProject.value) return 0
    const fromProj = projects.value.find(p => p.id === fromProjectId)
    if (!fromProj || !fromProj.dataSources) return 0
    
    let count = 0
    for (const ds of fromProj.dataSources) {
      // 避免重复同名数据源
      if (!currentProject.value.dataSources.find(d => d.name === ds.name)) {
        const newDs = { ...ds, id: `ds_${nanoid(8)}` }
        currentProject.value.dataSources.push(newDs)
        count++
      }
    }
    if (count > 0) _persist()
    return count
  }

  function saveProject(widgets) {
    if (!currentProject.value) return
    currentProject.value.savedAt = new Date().toISOString()
    // 兼容旧版：如果还有项目级 widgets，保存它
    if (widgets) currentProject.value.widgets = widgets
    const idx = projects.value.findIndex(p => p.id === currentProject.value.id)
    if (idx >= 0) {
      projects.value[idx] = { ...currentProject.value }
    }
    _persist()
  }

  function openProject(projectId) {
    return loadProject(projectId)
  }

  function closeProject() {
    currentProject.value = null
  }

  function updateProjectName(projectId, newName) {
    const proj = projects.value.find(p => p.id === projectId)
    if (proj) {
      proj.name = newName
      if (currentProject.value?.id === projectId) {
        currentProject.value.name = newName
      }
      _persist()
    }
  }

  // ========== 持久化 ==========

  function _persist() {
    persistence.save('projects', projects.value)
  }

  function loadProjects() {
    const data = persistence.load('projects', [])
    projects.value = data.map(_normalize)
  }

  function _normalize(project) {
    return {
      ...project,
      dataSources: Array.isArray(project?.dataSources) ? project.dataSources : [],
      dashboards: Array.isArray(project?.dashboards) ? project.dashboards : [],
      widgets: Array.isArray(project?.widgets) ? project.widgets : [],
      theme: project?.theme || 'dark-tech',
    }
  }

  // 初始化时自动加载
  loadProjects()

  return {
    projects,
    currentProject,
    hasProject,
    // 项目
    createProject,
    deleteProject,
    loadProject,
    // 看板
    getDashboards,
    createDashboard,
    deleteDashboard,
    getDashboard,
    saveDashboard,
    // 数据源
    addDataSource,
    removeDataSource,
    updateDataSource,
    copyDataSources,
    // 兼容
    saveProject,
    loadProjects,
    openProject,
    closeProject,
    updateProjectName,
  }
})
