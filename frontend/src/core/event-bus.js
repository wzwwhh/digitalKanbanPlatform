/**
 * 事件总线 - 模块间通信
 * 基于 mitt，提供类型安全的事件发布/订阅
 */
import mitt from 'mitt'

const emitter = mitt()

export default emitter

/**
 * 预定义事件名称
 */
export const Events = {
  // 组件事件
  WIDGET_SELECTED: 'widget:selected',
  WIDGET_DESELECTED: 'widget:deselected',
  WIDGET_ADDED: 'widget:added',
  WIDGET_REMOVED: 'widget:removed',
  WIDGET_UPDATED: 'widget:updated',

  // AI 事件
  AI_THINKING: 'ai:thinking',
  AI_RESPONSE: 'ai:response',
  AI_ERROR: 'ai:error',

  // 主题事件
  THEME_CHANGED: 'theme:changed',

  // 画布事件
  CANVAS_CLICK: 'canvas:click',
  CANVAS_DROP: 'canvas:drop',
}
