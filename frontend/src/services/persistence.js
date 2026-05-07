/**
 * 持久化适配器 - 统一 save/load 接口
 *
 * 支持两种模式:
 * 1. localStorage (默认) - 本地存储，适合开发环境
 * 2. API - 服务器存储，适合生产环境
 *
 * 通过环境变量 VITE_STORAGE_MODE 控制:
 * - "local" (默认) - 使用 localStorage
 * - "api" - 使用后端 API
 */

const PREFIX = 'dkp_'
const STORAGE_MODE = import.meta.env.VITE_STORAGE_MODE || 'local'
const BASE_URL = import.meta.env.BASE_URL || '/'
const API_BASE = import.meta.env.VITE_API_BASE || `${BASE_URL.replace(/\/$/, '')}/api`

// ========== localStorage 实现 ==========

const localStorageAdapter = {
  save(key, data) {
    try {
      localStorage.setItem(PREFIX + key, JSON.stringify(data))
      return true
    } catch (e) {
      console.error(`[persistence] 保存失败 (${key}):`, e)
      return false
    }
  },

  load(key, defaultValue = null) {
    try {
      const raw = localStorage.getItem(PREFIX + key)
      if (raw === null) return defaultValue
      return JSON.parse(raw)
    } catch (e) {
      console.error(`[persistence] 加载失败 (${key}):`, e)
      return defaultValue
    }
  },

  remove(key) {
    localStorage.removeItem(PREFIX + key)
  },

  has(key) {
    return localStorage.getItem(PREFIX + key) !== null
  },
}

// ========== API 实现 ==========

const apiAdapter = {
  async save(key, data) {
    // API 模式下，projects 数据通过专门的 API 保存
    // 这里只是兼容接口，实际保存在 project store 中调用具体 API
    console.warn('[persistence] API 模式下不应直接调用 save，请使用 projectStore 的方法')
    return true
  },

  async load(key, defaultValue = null) {
    if (key === 'projects') {
      try {
        const response = await fetch(`${API_BASE}/projects/`)
        if (!response.ok) {
          console.error('[persistence] 加载项目列表失败:', response.status)
          return defaultValue
        }

        const contentType = response.headers.get('content-type') || ''
        if (!contentType.includes('application/json')) {
          const text = await response.text()
          console.error('[persistence] 期望 JSON，但收到非 JSON 响应:', text.slice(0, 120))
          return defaultValue
        }

        const projects = await response.json()

        // 确保返回的是数组
        if (!Array.isArray(projects)) {
          console.error('[persistence] API 返回格式错误，期望数组，实际:', projects)
          return defaultValue
        }

        // 转换 API 格式到前端格式
        return projects.map(p => ({
          id: p.id,
          name: p.name,
          description: p.description,
          dataSources: [],  // 数据源在加载项目详情时获取
          dashboards: [],   // 看板在加载项目详情时获取
          created_at: p.created_at,
          updated_at: p.updated_at
        }))
      } catch (e) {
        console.error('[persistence] 加载项目列表失败:', e)
        return defaultValue
      }
    }

    return defaultValue
  },

  remove(key) {
    console.warn('[persistence] API 模式下不支持 remove，请使用 projectStore 的删除方法')
  },

  has(key) {
    console.warn('[persistence] API 模式下不支持 has')
    return false
  },
}

// ========== 导出统一接口 ==========

export const persistence = STORAGE_MODE === 'api' ? apiAdapter : localStorageAdapter

// 导出当前模式（用于调试）
export const storageMode = STORAGE_MODE

console.log(`[persistence] 存储模式: ${STORAGE_MODE}`)
