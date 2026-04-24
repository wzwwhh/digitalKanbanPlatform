/**
 * Theme Store - 主题管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getAllThemes } from '../core/registry'

export const useThemeStore = defineStore('theme', () => {
  const currentTheme = ref('dark-tech')

  /**
   * 应用主题 - 将主题变量写入 CSS 自定义属性
   */
  function applyTheme(themeName) {
    const themes = getAllThemes()
    const theme = themes[themeName]
    if (!theme) {
      console.warn(`主题 "${themeName}" 未注册`)
      return
    }

    currentTheme.value = themeName

    // 将主题变量应用到 :root
    const root = document.documentElement
    Object.entries(theme.vars).forEach(([key, value]) => {
      root.style.setProperty(key, value)
    })
  }

  /**
   * 初始化主题
   */
  function initTheme() {
    applyTheme(currentTheme.value)
  }

  return {
    currentTheme,
    applyTheme,
    initTheme,
  }
})
