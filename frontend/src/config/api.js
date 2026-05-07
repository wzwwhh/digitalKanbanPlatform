// API 基础路径配置
// 开发环境：使用相对路径 /api（由 Vite proxy 代理到后端）
// 生产环境：使用完整路径 /kanban/api（匹配 base 路径）

const isDev = import.meta.env.DEV
const base = import.meta.env.BASE_URL || '/'

// 开发环境直接用 /api（走 proxy）；生产环境使用 BASE_URL 拼接后的路径
export const API_BASE = isDev ? '/api' : `${base.replace(/\/$/, '')}/api`

// 辅助函数：构建完整 API 路径
export function apiUrl(path) {
  // 确保 path 以 / 开头
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE}${cleanPath}`
}
