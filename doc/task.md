# AI 看板平台 - 任务追踪

## 第一批: 骨架

### 模块 A: 项目脚手架
- `[x]` A1. Vue 3 + Vite 初始化
- `[x]` A2. 安装前端依赖 (pinia, vue-echarts, echarts, mitt, nanoid, vue-router)
- `[x]` A3. FastAPI 后端初始化 (main.py + CORS + 3个路由桩)
- `[x]` A4. Vite 代理配置
- `[x]` A5. 完整目录结构建立

### 模块 B: 核心引擎
- `[x]` B1. Command 系统 (command.js - execute/undo/redo/batch)
- `[x]` B2. 注册中心 (registry.js - widget/agent/theme/datasource)
- `[x]` B3. 事件总线 (event-bus.js - mitt + 预定义事件)
- `[x]` B4. Project Store (项目管理 + 数据源列表 + 持久化)
- `[x]` B5. Dashboard Store (widgets CRUD + 选中态)
- `[x]` B6. History Store (undo/redo 栈)
- `[x]` B7. Theme Store (CSS 变量主题切换)
- `[x]` B8. DataSource Store (运行时数据缓存)

### 模块 C: 组件 (前5个)
- `[x]` C1. WidgetWrapper (选中 + 拖拽 + 四角缩放)
- `[x]` C2. 组件注册表 (15个组件 schema 全定义，懒加载)
- `[x]` C3. KpiCard (指标卡 + 趋势箭头)
- `[x]` C4. LineChart (折线图 + 平滑/面积选项)
- `[x]` C5. BarChart (柱状图 + 堆叠/横向选项)
- `[x]` C6. PieChart (饼图 + 环形/标签选项)
- `[x]` C7. TextBlock (文本 + 字号/对齐/颜色)
- `[x]` 10个占位组件已创建

### 模块 D: 工作区
- `[x]` D1. 画布渲染 (1920x1080 + 网格背景)
- `[x]` D2. 拖拽移动 (通过 WidgetWrapper)
- `[x]` D3. 缩放手柄 (四角拖拽缩放)
- `[x]` D4. 组件选中 (蓝色描边 + 取消选中)
- `[x]` D5. 属性编辑面板 (PropEditor.vue)
- `[x]` D6. 保存/恢复 (localStorage)

### 已额外完成
- `[x]` ProjectHome.vue (项目首页 + 两种模式)
- `[x]` AppLayout.vue (整体布局 + 顶栏 + 侧栏)
- `[x]` 3套主题预设 (dark-tech / light-biz / cyber-neon)
- `[x]` Materials Store (素材过滤逻辑)

---

## 第二批: 数据与 AI 接入

### 模块 E: 数据源配置
- `[x]` E1. DataSourceConfig.vue (数据源配置面板)
- `[x]` E2. API 探测服务后端 (api_probe.py)
- `[x]` E3. 前端与 Project Store 联动

### 模块 G: AI 系统
- `[x]` G1. 意图路由机制 (正则 -> 关键词 -> LLM Agent)
- `[x]` G2. Kimi/Moonshot API 封装 (kimi.py)
- `[x]` G3. Agent 基类设计 (上下文序列化)
- `[x]` G4. Scene Agent (基于数据源生成完整布局)
- `[x]` G5. Component Agent (单组件增删改)
- `[x]` G9. AI 对话面板前端 (AiChat.vue)

### 模块 I & J (待办):
- `[ ]` 导出系统 (生成独立 HTML 或 Vue 代码)
- `[ ]` 数据库直连 (MySQL/PG 探测与查询)
