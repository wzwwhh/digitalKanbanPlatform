<template>
  <div class="map-chart">
    <div v-if="p.props.title" class="chart-title">{{ p.props.title }}</div>
    <div ref="chartRef" class="chart-container"></div>
    <div v-if="loading" class="loading-overlay">加载地图数据中...</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const p = defineProps({
  widget: { type: Object, default: () => ({}) },
  props: { type: Object, default: () => ({}) },
  data: { type: Array, default: () => [] },
})

const chartRef = ref(null)
let chartInstance = null
const loading = ref(true)

// 全局缓存地图注册状态，避免重复拉取
if (!window._mapRegistered) {
  window._mapRegistered = false
}

async function initMap() {
  if (!window._mapRegistered) {
    try {
      const res = await fetch('https://registry.npmmirror.com/echarts/4.9.0/files/map/json/china.json')
      const geoJson = await res.json()
      echarts.registerMap('china', geoJson)
      window._mapRegistered = true
    } catch (err) {
      console.error('Failed to load China map geojson', err)
      // 回退方案：如果在无网络环境下，这里最好使用本地的 json 文件
      alert('地图数据加载失败，请检查网络（需要访问 npmmirror 接口）')
    }
  }
  loading.value = false
  initChart()
}

function initChart() {
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  updateChart()
}

function updateChart() {
  if (!chartInstance) return

  function normalizeProvinceName(name) {
    if (!name) return ''
    // 内蒙古特殊处理：ECharts GeoJSON 里它的标准名是"内蒙古自治区"，不能剥离
    if (name.startsWith('内蒙古')) return '内蒙古自治区'
    return name
      .replace(/维吾尔自治区$/, '')
      .replace(/壮族自治区$/, '')
      .replace(/回族自治区$/, '')
      .replace(/自治区$/, '')
      .replace(/特别行政区$/, '')
      .replace(/省$/, '')
      .replace(/市$/, '')
  }

  let mapData = []
  if (p.data && p.data.length > 0) {
    mapData = p.data.map(item => ({
      name: normalizeProvinceName(item.name),
      value: Number(item.value) || 0
    }))
  } else {
    // 默认假数据
    mapData = [
      { name: '北京', value: 100 },
      { name: '上海', value: 200 },
      { name: '广东', value: 300 },
      { name: '浙江', value: 250 },
      { name: '四川', value: 150 },
      { name: '江苏', value: 280 },
    ]
  }

  // 计算最大值以动态设置 visualMap
  const maxVal = Math.max(...mapData.map(d => d.value), 500)

  // 各省份大致中心坐标，用于渲染发光波纹
  const geoCoordMap = {
    '北京': [116.405, 39.905], '天津': [117.190, 39.125], '河北': [114.502, 38.046],
    '山西': [112.549, 37.864], '内蒙古自治区': [111.670, 40.818], '辽宁': [123.429, 41.796],
    '吉林': [125.324, 43.886], '黑龙江': [126.642, 45.756], '上海': [121.472, 31.231],
    '江苏': [118.767, 32.041], '浙江': [120.153, 30.287], '安徽': [117.283, 31.861],
    '福建': [119.306, 26.075], '江西': [115.892, 28.676], '山东': [117.000, 36.675],
    '河南': [113.665, 34.766], '湖北': [114.298, 30.584], '湖南': [112.982, 28.194],
    '广东': [113.280, 23.125], '广西': [108.320, 22.824], '海南': [110.331, 20.031],
    '重庆': [106.505, 29.533], '四川': [104.065, 30.659], '贵州': [106.713, 26.572],
    '云南': [102.712, 25.040], '西藏': [91.114, 29.646], '陕西': [108.948, 34.263],
    '甘肃': [103.823, 36.058], '青海': [101.778, 36.623], '宁夏': [106.278, 38.466],
    '新疆': [87.617, 43.792], '台湾': [121.509, 25.044], '香港': [114.165, 22.275],
    '澳门': [113.549, 22.192]
  }

  const scatterData = mapData
    .filter(d => geoCoordMap[d.name] && d.value > 0)
    .map(d => ({
      name: d.name,
      value: [...geoCoordMap[d.name], d.value] // [经度, 纬度, 数值]
    }))

  const baseColor = p.props.color || '#00d4ff'
  const hexToRgba = (hex, alpha) => {
    let r = 0, g = 212, b = 255;
    if (hex && hex.startsWith('#')) {
      let h = hex.slice(1);
      if (h.length === 3) h = [...h].map(x => x + x).join('');
      if (h.length === 6) {
        r = parseInt(h.slice(0, 2), 16);
        g = parseInt(h.slice(2, 4), 16);
        b = parseInt(h.slice(4, 6), 16);
      }
    }
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
  const color01 = hexToRgba(baseColor, 0.1)
  const color04 = hexToRgba(baseColor, 0.4)
  const color09 = hexToRgba(baseColor, 0.9)

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: function (params) {
        if (params.seriesType === 'effectScatter') return params.data.name + ': ' + params.data.value[2]
        return params.name + ': ' + (params.value || 0)
      }
    },
    // 底层投影，实现阴影和立体感
    geo: {
      map: 'china',
      roam: false,
      zoom: 1.2,
      label: {
        show: true,
        color: 'rgba(255,255,255,0.7)',
        fontSize: 10
      },
      itemStyle: {
        areaColor: '#0a143b', // 底层深色
        borderColor: baseColor, // 动态边界色
        borderWidth: 1,
        shadowColor: color04,
        shadowBlur: 15,
        shadowOffsetY: 5
      },
      emphasis: {
        label: { color: '#fff', show: true },
        itemStyle: {
          areaColor: baseColor, // 悬浮高亮色
          shadowBlur: 20,
          shadowColor: baseColor
        }
      }
    },
    visualMap: {
      min: 0,
      max: maxVal,
      left: 'left',
      bottom: 'bottom',
      text: ['高', '低'],
      inRange: {
        color: [color01, color09]
      },
      textStyle: { color: '#ccc' },
      calculable: true,
      show: p.props.showVisualMap !== false,
      seriesIndex: 0 // 只对 map 系列生效，不影响散点
    },
    series: [
      {
        name: '地域数据',
        type: 'map',
        geoIndex: 0, // 绑定到 geo
        data: mapData
      },
      {
        name: '高亮节点',
        type: 'effectScatter',
        coordinateSystem: 'geo',
        zlevel: 2,
        rippleEffect: {
          period: 3,
          brushType: 'stroke',
          scale: 5
        },
        label: {
          show: false // 不重复显示文字，交由 geo 处理
        },
        symbolSize: function (val) {
          // 根据数值动态计算发光点大小
          return Math.max(8, (val[2] / maxVal) * 20)
        },
        itemStyle: {
          color: '#00FF7F', // 荧光绿波纹
          shadowBlur: 10,
          shadowColor: '#00FF7F'
        },
        data: scatterData
      }
    ]
  }

  chartInstance.setOption(option)
}

onMounted(() => {
  initMap()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
  }
})

function handleResize() {
  if (chartInstance) chartInstance.resize()
}

// 监听配置和数据变化
watch(() => [p.props, p.data], () => {
  if (!loading.value) updateChart()
}, { deep: true })

// 监听组件尺寸变化（画布拖拽调整大小时需要重绘）
watch(() => p.widget?.size, () => {
  handleResize()
}, { deep: true })
</script>

<style scoped>
.map-chart {
  width: 100%; height: 100%;
  display: flex; flex-direction: column;
  position: relative;
}
.chart-title {
  font-size: 14px; font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
  text-align: center;
}
.chart-container {
  flex: 1; min-height: 0;
  width: 100%;
}
.loading-overlay {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background: rgba(0,0,0,0.5); color: #fff; font-size: 14px;
  border-radius: 6px;
}
</style>
