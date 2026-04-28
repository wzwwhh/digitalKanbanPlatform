/**
 * Custom Templates Store - 自定义组件模板管理
 *
 * 用户可基于内置组件创建预设模板（预填属性/颜色/数据），
 * 在编辑器素材库中直接使用。
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { nanoid } from 'nanoid'
import { persistence } from '../services/persistence'

export const useCustomTemplatesStore = defineStore('customTemplates', () => {
  const templates = ref([])

  function loadTemplates() {
    templates.value = persistence.load('custom_templates', [])
  }

  function addTemplate(template) {
    const t = {
      id: `tpl_${nanoid(8)}`,
      ...template,
      createdAt: new Date().toISOString(),
    }
    templates.value.push(t)
    _persist()
    return t
  }

  function updateTemplate(id, updates) {
    const idx = templates.value.findIndex(t => t.id === id)
    if (idx >= 0) {
      templates.value[idx] = { ...templates.value[idx], ...updates }
      _persist()
    }
  }

  function deleteTemplate(id) {
    templates.value = templates.value.filter(t => t.id !== id)
    _persist()
  }

  function _persist() {
    persistence.save('custom_templates', templates.value)
  }

  // 初始化加载
  loadTemplates()

  return {
    templates,
    loadTemplates,
    addTemplate,
    updateTemplate,
    deleteTemplate,
  }
})
