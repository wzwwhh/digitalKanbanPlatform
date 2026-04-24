/**
 * Project Store - 项目管理（名称、数据源、模式）
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { nanoid } from 'nanoid'

export const useProjectStore = defineStore('project', () => {
  // 当前项目
  const currentProject = ref(null)
  // 项目列表（localStorage 持久化）
  const projects = ref([])

  // 是否有项目打开
  const hasProject = computed(() => currentProject.value !== null)

  /**
   * 创建新项目
   * @param {string} name - 项目名称
   * @param {'data-first'|'design-first'} mode - 工作模式
   */
  function createProject(name, mode = 'data-first') {
    const project = {
      id: `proj_${nanoid(10)}`,
      name,
      mode,
      dataSources: [],
      theme: 'dark-tech',
      createdAt: new Date().toISOString(),
      savedAt: null,
    }
    currentProject.value = project
    return project
  }

  /**
   * 添加数据源到当前项目
   */
  function addDataSource(ds) {
    if (!currentProject.value) return
    const dataSource = {
      id: `ds_${nanoid(8)}`,
      ...ds,
    }
    currentProject.value.dataSources.push(dataSource)
    return dataSource
  }

  /**
   * 删除数据源
   */
  function removeDataSource(dsId) {
    if (!currentProject.value) return
    currentProject.value.dataSources = currentProject.value.dataSources.filter(
      ds => ds.id !== dsId
    )
  }

  /**
   * 保存项目到 localStorage
   */
  function saveProject(widgets) {
    if (!currentProject.value) return
    currentProject.value.savedAt = new Date().toISOString()

    const saveData = {
      ...currentProject.value,
      widgets,
    }

    // 更新或添加到项目列表
    const idx = projects.value.findIndex(p => p.id === saveData.id)
    if (idx >= 0) {
      projects.value[idx] = saveData
    } else {
      projects.value.push(saveData)
    }

    localStorage.setItem('dkp_projects', JSON.stringify(projects.value))
  }

  /**
   * 加载项目列表
   */
  function loadProjects() {
    try {
      const data = localStorage.getItem('dkp_projects')
      if (data) {
        projects.value = JSON.parse(data)
      }
    } catch (e) {
      console.error('加载项目列表失败:', e)
    }
  }

  /**
   * 打开已有项目
   */
  function openProject(projectId) {
    const project = projects.value.find(p => p.id === projectId)
    if (project) {
      const { widgets, ...projectMeta } = project
      currentProject.value = projectMeta
      return widgets || []
    }
    return []
  }

  /**
   * 关闭当前项目
   */
  function closeProject() {
    currentProject.value = null
  }

  return {
    currentProject,
    projects,
    hasProject,
    createProject,
    addDataSource,
    removeDataSource,
    saveProject,
    loadProjects,
    openProject,
    closeProject,
  }
})
