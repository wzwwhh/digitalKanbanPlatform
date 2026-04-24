/**
 * DataSource Store - 数据源绑定状态
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useDataSourceStore = defineStore('datasource', () => {
  // 运行时数据缓存（数据源 ID → 最新数据）
  const dataCache = ref({})
  // 轮询定时器
  const pollingTimers = ref({})

  /**
   * 更新缓存数据
   */
  function setData(sourceId, data) {
    dataCache.value[sourceId] = {
      data,
      updatedAt: Date.now(),
    }
  }

  /**
   * 获取缓存数据
   */
  function getData(sourceId) {
    return dataCache.value[sourceId]?.data || null
  }

  /**
   * 清理所有轮询
   */
  function clearAllPolling() {
    Object.values(pollingTimers.value).forEach(timer => clearInterval(timer))
    pollingTimers.value = {}
  }

  return {
    dataCache,
    pollingTimers,
    setData,
    getData,
    clearAllPolling,
  }
})
