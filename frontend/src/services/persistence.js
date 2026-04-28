/**
 * 持久化适配器 - 统一 save/load 接口
 *
 * 当前: localStorage 实现
 * 将来: 替换为 API 调用，只需改这个文件
 */

const PREFIX = 'dkp_'

export const persistence = {
  /**
   * 保存数据
   * @param {string} key - 存储键
   * @param {any} data - 要保存的数据
   */
  save(key, data) {
    try {
      localStorage.setItem(PREFIX + key, JSON.stringify(data))
      return true
    } catch (e) {
      console.error(`[persistence] 保存失败 (${key}):`, e)
      return false
    }
  },

  /**
   * 加载数据
   * @param {string} key - 存储键
   * @param {any} defaultValue - 默认值
   * @returns {any}
   */
  load(key, defaultValue = null) {
    try {
      const raw = localStorage.getItem(PREFIX + key)
      if (raw === null) return defaultValue
      return JSON.parse(raw)
    } catch (e) {
      console.error(`[persistence] 加载失败 (${key}):`, e)
      return defaultValue
    }
  },

  /**
   * 删除数据
   * @param {string} key
   */
  remove(key) {
    localStorage.removeItem(PREFIX + key)
  },

  /**
   * 检查键是否存在
   * @param {string} key
   * @returns {boolean}
   */
  has(key) {
    return localStorage.getItem(PREFIX + key) !== null
  },
}
