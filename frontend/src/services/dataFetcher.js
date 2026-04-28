/**
 * DataFetcher - 从真实 API 获取数据并按 mapping 提取字段
 *
 * 用于组件级数据绑定：widget.dataSource → fetchDataSource() → 真实数据
 */

/**
 * 根据组件的 dataSource 配置获取真实数据
 *
 * @param {Object} dataSource - 组件的数据源配置 { sourceId, mapping }
 * @param {Array} projectDataSources - 项目所有数据源列表
 * @returns {Object|null} 提取后的数据
 */
export async function fetchWidgetData(dataSource, projectDataSources) {
  if (!dataSource?.sourceId) return null

  // 从项目数据源列表中找到配置
  const config = (projectDataSources || []).find(ds => ds.id === dataSource.sourceId)
  if (!config) return null

  // 数据库类型：通过后端 SQL 查询
  if (config.type === 'database') {
    return fetchDatabaseData(config, dataSource)
  }

  // API 类型：直接 fetch URL
  if (!config.url) return null

  try {
    const resp = await fetch(config.url, {
      method: config.method || 'GET',
      headers: config.headers || {},
    })
    if (!resp.ok) return null

    const raw = await resp.json()

    // 按 dataPath 提取数据数组（如 "data" → raw.data）
    let data = raw
    if (config.dataPath) {
      const parts = config.dataPath.split('.')
      for (const part of parts) {
        data = data?.[part]
        if (data === undefined) break
      }
    }

    // 如果 data 是对象（如 KPI），直接返回
    if (!Array.isArray(data)) {
      return { raw: data, rows: null, mapping: dataSource.mapping || {} }
    }

    // 如果 data 是数组，按 mapping 提取
    const mapping = dataSource.mapping || {}
    return {
      raw: data,
      rows: data,
      mapping,
      // 便捷方法：提取某个字段的值数组
      getColumn: (field) => data.map(row => row[field]),
      // 便捷方法：获取第一条记录的某个字段
      getValue: (field) => data[0]?.[field],
    }
  } catch (err) {
    console.warn(`[DataFetcher] 获取数据失败 (${config.url}):`, err.message)
    return null
  }
}

/**
 * 从 KPI 类数据源获取单个指标值
 */
export async function fetchKpiValue(dataSource, projectDataSources, field) {
  const result = await fetchWidgetData(dataSource, projectDataSources)
  if (!result) return null

  // KPI 数据通常是单个对象
  if (result.raw && !Array.isArray(result.raw)) {
    return result.raw[field]
  }
  // 如果是数组，取第一条
  if (result.rows?.length > 0) {
    return result.rows[0][field]
  }
  return null
}

/**
 * 从数据库数据源获取数据（通过后端 SQL 查询）
 */
async function fetchDatabaseData(config, dataSource) {
  try {
    const sql = config.sql || `SELECT * FROM ${config.table}`
    const resp = await fetch('/api/data/db/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql }),
    })
    if (!resp.ok) return null

    const result = await resp.json()
    if (!result.success) return null

    const data = result.data || []
    const mapping = dataSource.mapping || {}

    // 如果只有 1 行且是 KPI 类数据
    if (data.length === 1 && !Array.isArray(data[0])) {
      return { raw: data[0], rows: data, mapping }
    }

    return {
      raw: data,
      rows: data,
      mapping,
      getColumn: (field) => data.map(row => row[field]),
      getValue: (field) => data[0]?.[field],
    }
  } catch (err) {
    console.warn(`[DataFetcher] 数据库查询失败 (${config.table}):`, err.message)
    return null
  }
}
