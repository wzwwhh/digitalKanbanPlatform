/**
 * 主题注册表
 */
import { registerTheme } from '../core/registry'
import darkTech from './dark-tech'
import lightBiz from './light-biz'
import cyberNeon from './cyber-neon'
import minimalWhite from './minimal-white'
import forestGreen from './forest-green'

// 注册所有主题
registerTheme('dark-tech', darkTech)
registerTheme('light-biz', lightBiz)
registerTheme('cyber-neon', cyberNeon)
registerTheme('minimal-white', minimalWhite)
registerTheme('forest-green', forestGreen)

export { darkTech, lightBiz, cyberNeon, minimalWhite, forestGreen }
