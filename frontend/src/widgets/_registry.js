/**
 * 组件注册表 - 所有看板组件的 type → component/schema/defaultSize 映射
 *
 * 新增组件只需：1) 写 .vue 文件  2) 在这里加一行注册
 */
import { registerWidget } from '../core/registry'

// 懒加载组件（避免首屏加载全部）
const widgetDefs = {
  kpi: {
    component: () => import('./KpiCard.vue'),
    label: 'KPI 指标卡',
    icon: '📊',
    category: '指标',
    defaultSize: { w: 280, h: 160 },
    schema: {
      title: { type: 'string', label: '标题', default: 'KPI 指标' },
      value: { type: 'string', label: '数值', default: '0' },
      unit: { type: 'string', label: '单位', default: '' },
      trend: { type: 'select', label: '趋势', options: ['up', 'down', 'flat'], default: 'flat' },
      color: { type: 'color', label: '强调色', default: '' },
    }
  },
  line: {
    component: () => import('./LineChart.vue'),
    label: '折线图',
    icon: '📈',
    category: '图表',
    defaultSize: { w: 560, h: 300 },
    schema: {
      title: { type: 'string', label: '标题', default: '折线图' },
      smooth: { type: 'boolean', label: '平滑曲线', default: true },
      area: { type: 'boolean', label: '面积填充', default: false },
    }
  },
  bar: {
    component: () => import('./BarChart.vue'),
    label: '柱状图',
    icon: '📊',
    category: '图表',
    defaultSize: { w: 400, h: 300 },
    schema: {
      title: { type: 'string', label: '标题', default: '柱状图' },
      stack: { type: 'boolean', label: '堆叠', default: false },
      horizontal: { type: 'boolean', label: '横向', default: false },
    }
  },
  pie: {
    component: () => import('./PieChart.vue'),
    label: '饼图',
    icon: '🍩',
    category: '图表',
    defaultSize: { w: 300, h: 300 },
    schema: {
      title: { type: 'string', label: '标题', default: '饼图' },
      donut: { type: 'boolean', label: '环形', default: false },
      showLabel: { type: 'boolean', label: '显示标签', default: true },
    }
  },
  text: {
    component: () => import('./TextBlock.vue'),
    label: '标题文本',
    icon: '📝',
    category: '文本',
    defaultSize: { w: 400, h: 80 },
    schema: {
      content: { type: 'string', label: '内容', default: '标题文本' },
      fontSize: { type: 'number', label: '字号', default: 24 },
      align: { type: 'select', label: '对齐', options: ['left', 'center', 'right'], default: 'center' },
      color: { type: 'color', label: '颜色', default: '' },
    }
  },
  // ---------- 以下组件后续实现 ----------
  'number-flip': {
    component: () => import('./NumberFlip.vue'),
    label: '数字翻牌',
    icon: '🔢',
    category: '指标',
    defaultSize: { w: 260, h: 140 },
    schema: {
      title: { type: 'string', label: '标题', default: '数字翻牌' },
      value: { type: 'number', label: '数值', default: 0 },
      prefix: { type: 'string', label: '前缀', default: '' },
      suffix: { type: 'string', label: '后缀', default: '' },
    }
  },
  progress: {
    component: () => import('./ProgressRing.vue'),
    label: '进度环',
    icon: '⭕',
    category: '指标',
    defaultSize: { w: 200, h: 200 },
    schema: {
      title: { type: 'string', label: '标题', default: '进度' },
      percent: { type: 'number', label: '百分比', default: 75 },
      color: { type: 'color', label: '颜色', default: '' },
    }
  },
  gauge: {
    component: () => import('./GaugeChart.vue'),
    label: '仪表盘',
    icon: '🎯',
    category: '图表',
    defaultSize: { w: 300, h: 280 },
    schema: {
      title: { type: 'string', label: '标题', default: '仪表盘' },
      value: { type: 'number', label: '数值', default: 50 },
      min: { type: 'number', label: '最小值', default: 0 },
      max: { type: 'number', label: '最大值', default: 100 },
    }
  },
  radar: {
    component: () => import('./RadarChart.vue'),
    label: '雷达图',
    icon: '🕸️',
    category: '图表',
    defaultSize: { w: 350, h: 320 },
    schema: {
      title: { type: 'string', label: '标题', default: '雷达图' },
    }
  },
  scatter: {
    component: () => import('./ScatterChart.vue'),
    label: '散点图',
    icon: '⚬',
    category: '图表',
    defaultSize: { w: 450, h: 320 },
    schema: {
      title: { type: 'string', label: '标题', default: '散点图' },
      xName: { type: 'string', label: 'X轴名称', default: '' },
      yName: { type: 'string', label: 'Y轴名称', default: '' },
    }
  },
  table: {
    component: () => import('./DataTable.vue'),
    label: '数据表格',
    icon: '📋',
    category: '数据',
    defaultSize: { w: 500, h: 320 },
    schema: {
      title: { type: 'string', label: '标题', default: '数据表格' },
      sortable: { type: 'boolean', label: '可排序', default: true },
    }
  },
  ranking: {
    component: () => import('./RankingList.vue'),
    label: '排行榜',
    icon: '🏆',
    category: '数据',
    defaultSize: { w: 360, h: 400 },
    schema: {
      title: { type: 'string', label: '标题', default: '排行榜' },
      showBar: { type: 'boolean', label: '显示进度条', default: true },
      maxItems: { type: 'number', label: '最多显示', default: 10 },
    }
  },
  clock: {
    component: () => import('./ClockWidget.vue'),
    label: '时钟',
    icon: '🕐',
    category: '装饰',
    defaultSize: { w: 200, h: 100 },
    schema: {
      format: { type: 'select', label: '格式', options: ['24h', '12h'], default: '24h' },
      showDate: { type: 'boolean', label: '显示日期', default: true },
    }
  },
  marquee: {
    component: () => import('./MarqueeText.vue'),
    label: '滚动字幕',
    icon: '📜',
    category: '文本',
    defaultSize: { w: 600, h: 60 },
    schema: {
      text: { type: 'string', label: '内容', default: '滚动字幕内容' },
      speed: { type: 'number', label: '速度', default: 50 },
    }
  },
  'border-box': {
    component: () => import('./BorderBox.vue'),
    label: '装饰边框',
    icon: '🔲',
    category: '装饰',
    defaultSize: { w: 400, h: 300 },
    schema: {
      title: { type: 'string', label: '标题', default: '' },
      style: { type: 'select', label: '样式', options: ['tech-1', 'tech-2', 'simple'], default: 'tech-1' },
      glowing: { type: 'boolean', label: '发光效果', default: true },
    }
  },
}

// 批量注册
Object.entries(widgetDefs).forEach(([type, config]) => {
  registerWidget(type, config)
})

export default widgetDefs
