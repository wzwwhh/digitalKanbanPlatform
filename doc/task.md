# AI 看板平台 - 任务追踪

> 最后更新: 2026-04-24

---

## 第一批: 骨架 ✅ 已完成

### 模块 A: 项目脚手架
- `[x]` A1. Vue 3 + Vite 初始化
- `[x]` A2. 安装前端依赖 (pinia, vue-echarts, echarts, mitt, nanoid)
- `[x]` A3. FastAPI 后端初始化 (main.py + CORS + 3个路由)
- `[x]` A4. Vite 代理配置 (/api → localhost:8000)
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

### 模块 C: 组件
- `[x]` C1. WidgetWrapper (选中 + 拖拽 + 四角缩放)
- `[x]` C2. 组件注册表 (15个组件 schema 全定义，懒加载)
- `[x]` C3. KpiCard (指标卡 + 趋势箭头)
- `[x]` C4. LineChart (折线图 + 平滑/面积选项)
- `[x]` C5. BarChart (柱状图 + 堆叠/横向选项)
- `[x]` C6. PieChart (饼图 + 环形/标签选项)
- `[x]` C7. TextBlock (文本 + 字号/对齐/颜色)
- `[x]` 10个占位组件已创建 (基础 UI，无 ECharts)

### 模块 D: 工作区
- `[x]` D1. 画布渲染 (1920x1080 + 网格背景)
- `[x]` D2. 拖拽移动 (通过 WidgetWrapper)
- `[x]` D3. 缩放手柄 (四角拖拽缩放)
- `[x]` D4. 组件选中 (蓝色描边 + 取消选中)
- `[x]` D5. 属性编辑面板 (PropEditor.vue - Schema 驱动)
- `[x]` D6. 保存/恢复 (localStorage)

### 额外完成
- `[x]` ProjectHome.vue (项目首页 + 两种模式入口)
- `[x]` AppLayout.vue (整体布局: 顶栏+左侧素材库+画布+右侧面板)
- `[x]` 3 套主题预设 (dark-tech / light-biz / cyber-neon)
- `[x]` Materials Store (素材过滤逻辑)

---

## 第二批: 数据 + AI ✅ 已完成

### 模块 E: 数据源配置
- `[x]` E1. DataSourceConfig.vue (数据源配置面板)
- `[x]` E2. API 探测服务后端 (api_probe.py - 解析 JSON 结构)
- `[x]` E3. 前端与 Project Store 联动 (添加/删除数据源)

### 模块 G: AI 系统
- `[x]` G1. 意图路由机制 (正则 → 关键词 → LLM Agent)
- `[x]` G2. Kimi/Moonshot API 封装 (kimi.py - 兼容 OpenAI SDK)
- `[x]` G3. Agent 基类设计 (base.py - 上下文序列化)
- `[x]` G4. Scene Agent (基于数据源生成完整看板布局)
- `[x]` G5. Component Agent (单组件增删改)
- `[x]` G9. AI 对话面板前端 (AiChat.vue - 消息流+快捷按钮+加载态)

### 模块 J: 导出 (基础版)
- `[x]` J1. HTML 单文件导出 (export.py - KPI/Text/Line/Bar/Pie)
- `[x]` J2. 自适应缩放 (fitCanvas)
- `[x]` J3. ECharts CDN 集成

---

## 第三批: 待开发 ⏳

### 模块 I: 数据库直连
- `[ ]` I1. DB 连接管理 (db_connector.py 已有桩)
- `[ ]` I2. SQL 执行服务
- `[ ]` I3. 数据库表/字段探测
- `[ ]` I4. 前端 DB 配置 UI (DataSourceConfig 已有入口)

### 模块 G 补全: 更多 Agent
- `[ ]` G6. 布局 Agent (排列/对齐/等距)
- `[ ]` G7. 数据 Agent (AI 自动映射字段到组件)
- `[ ]` G8. SQL 生成 Agent (用户描述 → AI 写 SQL)

### 模块 J 增强: 完整项目导出
- `[ ]` J4. 后端代理生成 (API 源 → FastAPI 代理路由)
- `[ ]` J5. 后端生成 (DB 源 → SQLAlchemy 查询)
- `[ ]` J6. README + API 文档生成
- `[ ]` J7. ZIP 打包下载
- `[ ]` J8. 启动脚本 (start.bat / start.sh)

### 组件补全
- `[ ]` 完善 DataTable (ECharts 或原生表格)
- `[ ]` 完善 NumberFlip (翻牌动画)
- `[ ]` 完善 ProgressRing (SVG 进度环)
- `[ ]` 完善 GaugeChart (ECharts 仪表盘)
- `[ ]` 完善 RadarChart (ECharts 雷达图)
- `[ ]` 完善 ScatterChart (ECharts 散点图)
- `[ ]` 完善 RankingList (排行榜动画)
- `[ ]` 完善 ClockWidget (实时时钟)
- `[ ]` 完善 MarqueeText (滚动字幕)
- `[ ]` 完善 BorderBox (装饰边框)

---

## 验收结果

| 测试项 | 结果 |
|--------|------|
| 首页创建项目 | ✅ 两种模式入口正常 |
| 画布交互 (拖拽/缩放/选中) | ✅ |
| Schema 驱动属性编辑 | ✅ |
| 主题切换 | ✅ 3 套即时生效 |
| 保存/恢复 | ✅ localStorage |
| AI 对话面板 | ✅ 快捷按钮 + 输入框 |
| AI 生成看板 (Kimi) | ✅ "做一个电商看板" → 8 个组件 |
| API 数据源探测 | ✅ 后端 200 OK |
| HTML 导出 | ✅ 单文件 + CDN + 自适应 |
