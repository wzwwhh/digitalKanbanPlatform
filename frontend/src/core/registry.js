/**
 * 插件注册中心 - 统一管理 widget / agent / theme / datasource 注册
 *
 * 扩展方式：在对应的 _registry.js 中注册即可，无需改动核心代码
 */

const registries = {
  widgets: {},
  agents: {},
  themes: {},
  datasources: {},
}

/**
 * 注册组件
 */
export function registerWidget(type, config) {
  registries.widgets[type] = config
}

/**
 * 注册 Agent
 */
export function registerAgent(name, config) {
  registries.agents[name] = config
}

/**
 * 注册主题
 */
export function registerTheme(name, config) {
  registries.themes[name] = config
}

/**
 * 注册数据源适配器
 */
export function registerDatasource(type, config) {
  registries.datasources[type] = config
}

/**
 * 获取注册项
 */
export function getWidget(type) {
  return registries.widgets[type]
}

export function getAllWidgets() {
  return { ...registries.widgets }
}

export function getAgent(name) {
  return registries.agents[name]
}

export function getAllAgents() {
  return { ...registries.agents }
}

export function getTheme(name) {
  return registries.themes[name]
}

export function getAllThemes() {
  return { ...registries.themes }
}

export function getDatasource(type) {
  return registries.datasources[type]
}

export default registries
