/**
 * 主题注册表
 */
import { registerTheme } from '../core/registry'
import darkTech from './dark-tech'
import lightBiz from './light-biz'
import cyberNeon from './cyber-neon'

// 注册所有主题
registerTheme('dark-tech', darkTech)
registerTheme('light-biz', lightBiz)
registerTheme('cyber-neon', cyberNeon)

export { darkTech, lightBiz, cyberNeon }
