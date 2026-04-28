/**
 * Dashboard Store - 画布上的组件列表和选中状态
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { nanoid } from 'nanoid'

export const useDashboardStore = defineStore('dashboard', () => {
  // 组件列表
  const widgets = ref([])
  // 当前选中的组件 ID
  const selectedId = ref(null)

  // 选中的组件对象
  const selectedWidget = computed(() => {
    if (!selectedId.value) return null
    return widgets.value.find(w => w.id === selectedId.value) || null
  })

  /**
   * 根据 ID 获取组件
   */
  function getWidgetById(id) {
    return widgets.value.find(w => w.id === id) || null
  }

  /**
   * 添加组件
   */
  function addWidget(widget) {
    // 确保有 ID
    if (!widget.id) {
      widget.id = `widget_${nanoid(10)}`
    }
    widgets.value.push({ ...widget })
  }

  /**
   * 更新组件
   */
  function updateWidget(id, updates) {
    const idx = widgets.value.findIndex(w => w.id === id)
    if (idx >= 0) {
      const widget = widgets.value[idx]
      // 深合并 props
      if (updates.props) {
        widget.props = { ...widget.props, ...updates.props }
      }
      if (updates.position) {
        widget.position = { ...widget.position, ...updates.position }
      }
      if (updates.size) {
        widget.size = { ...widget.size, ...updates.size }
      }
      if (updates.dataSource !== undefined) {
        widget.dataSource = updates.dataSource
      }
      if (updates.type !== undefined) {
        widget.type = updates.type
      }
    }
  }

  /**
   * 删除组件
   */
  function removeWidget(id) {
    widgets.value = widgets.value.filter(w => w.id !== id)
    if (selectedId.value === id) {
      selectedId.value = null
    }
  }

  /**
   * 选中组件
   */
  function selectWidget(id) {
    selectedId.value = id
  }

  /**
   * 取消选中
   */
  function deselectAll() {
    selectedId.value = null
  }

  /**
   * 批量设置组件（用于加载项目）
   */
  function setWidgets(newWidgets) {
    widgets.value = newWidgets.map(w => ({ ...w }))
  }

  /**
   * 清空画布
   */
  function clearAll() {
    widgets.value = []
    selectedId.value = null
  }

  return {
    widgets,
    selectedId,
    selectedWidget,
    getWidgetById,
    addWidget,
    updateWidget,
    removeWidget,
    selectWidget,
    deselectAll,
    setWidgets,
    clearAll,
  }
})
