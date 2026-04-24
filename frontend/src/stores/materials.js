/**
 * Materials Store - 素材库
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getAllWidgets } from '../core/registry'

export const useMaterialsStore = defineStore('materials', () => {
  const searchQuery = ref('')
  const activeCategory = ref('all')

  // 从注册表获取所有素材
  const allMaterials = computed(() => {
    const widgets = getAllWidgets()
    return Object.entries(widgets).map(([type, config]) => ({
      type,
      ...config,
    }))
  })

  // 分类列表
  const categories = computed(() => {
    const cats = new Set(allMaterials.value.map(m => m.category))
    return ['all', ...cats]
  })

  // 过滤后的素材
  const filteredMaterials = computed(() => {
    let result = allMaterials.value

    if (activeCategory.value !== 'all') {
      result = result.filter(m => m.category === activeCategory.value)
    }

    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      result = result.filter(m =>
        m.label.toLowerCase().includes(query) ||
        m.type.toLowerCase().includes(query)
      )
    }

    return result
  })

  return {
    searchQuery,
    activeCategory,
    allMaterials,
    categories,
    filteredMaterials,
  }
})
