/**
 * Theme Store - 主题管理 + 自定义主题库
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getAllThemes, registerTheme } from '../core/registry'
import { persistence } from '../services/persistence'
import emitter, { Events } from '../core/event-bus'

export const useThemeStore = defineStore('theme', () => {
  const savedTheme = typeof localStorage !== 'undefined' ? localStorage.getItem('dkp_theme') : null
  const currentTheme = ref(savedTheme || 'dark-tech')
  const currentBoardStyle = ref(savedTheme || 'dark-tech')

  // 自定义主题列表（持久化到 localStorage）
  const customThemes = ref([])
  // 触发 allThemes 重新计算的版本号（因为 getAllThemes() 返回普通对象，computed 无法感知）
  const _themeVersion = ref(0)

  /**
   * 应用系统主题 - 将主题变量写入 CSS 自定义属性
   */
  function applySystemTheme(themeName) {
    const themes = getAllThemes()
    const theme = themes[themeName]
    if (!theme) {
      console.warn(`主题 "${themeName}" 未注册`)
      return
    }

    currentTheme.value = themeName
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('dkp_theme', themeName)
    }

    // 将主题变量应用到 :root
    const root = document.documentElement
    Object.entries(theme.vars).forEach(([key, value]) => {
      root.style.setProperty(key, value)
    })

    emitter.emit(Events.THEME_CHANGED, { themeName })
  }

  /**
   * 应用看板风格
   */
  function applyBoardStyle(styleName) {
    currentBoardStyle.value = styleName
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('dkp_board_style', styleName)
    }
    emitter.emit(Events.THEME_CHANGED, { themeName: currentTheme.value, boardStyle: styleName })
  }

  /**
   * 兼容旧调用：同时作为系统主题与看板风格入口
   */
  function applyTheme(themeName) {
    applySystemTheme(themeName)
    applyBoardStyle(themeName)
  }

  /**
   * 初始化主题（含自定义主题加载）
   */
  function initTheme() {
    loadCustomThemes()
    applyTheme(currentTheme.value)
  }

  // ========== 自定义主题库 ==========

  /**
   * 保存自定义主题
   */
  function saveCustomTheme(name, vars) {
    if (customThemes.value.length >= 10) {
      console.warn('自定义主题数量已达上限(10个)')
      return null
    }
    const id = `custom-${Date.now()}`
    const theme = { label: name, vars }
    registerTheme(id, theme)
    customThemes.value.push({ id, label: name, vars })
    _persistCustomThemes()
    _themeVersion.value++  // 触发 allThemes 重新计算
    return id
  }

  /**
   * 删除自定义主题
   */
  function deleteCustomTheme(themeId) {
    customThemes.value = customThemes.value.filter(t => t.id !== themeId)
    _persistCustomThemes()
    _themeVersion.value++  // 触发 allThemes 重新计算
    if (currentTheme.value === themeId) {
      applyTheme('dark-tech')
    }
  }

  /**
   * 从 localStorage 加载自定义主题并注册
   */
  function loadCustomThemes() {
    const data = persistence.load('custom_themes', [])
    customThemes.value = data
    data.forEach(t => {
      registerTheme(t.id, { label: t.label, vars: t.vars })
    })
    _themeVersion.value++
  }

  function _persistCustomThemes() {
    persistence.save('custom_themes', customThemes.value)
  }

  /**
   * 获取全部可用主题列表（内置 + 自定义）
   * 依赖 _themeVersion 保证动态注册后 computed 会重新计算
   */
  const allThemes = computed(() => {
    void _themeVersion.value  // 触发 computed 依赖追踪
    const all = getAllThemes()
    return Object.entries(all).map(([id, theme]) => ({
      id,
      label: theme.label || id,
      isCustom: id.startsWith('custom-'),
      vars: theme.vars || {},
    }))
  })

  return {
    currentTheme,
    currentBoardStyle,
    customThemes,
    allThemes,
    applyTheme,
    applySystemTheme,
    applyBoardStyle,
    initTheme,
    // 自定义主题
    saveCustomTheme,
    deleteCustomTheme,
    loadCustomThemes,
  }
})
