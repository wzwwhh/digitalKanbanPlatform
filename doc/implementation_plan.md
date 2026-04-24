# AI 看板平台 - 完整实施规范 v3

> **项目目录**: `d:\学习\outputmsg\排课\digitalKanbanPlatform`
> **定位**: AI 看板生产系统 - "连上数据，说句话，导出来直接部署"
> **技术栈**: Vue 3 + Vite + Pinia | FastAPI + Python | Kimi (Moonshot) | ECharts 5

---

## 已确认的设计决策

| # | 决策 | 结论 | 理由 |
|---|------|------|------|
| 1 | AI 面板位置 | 右侧面板，与属性编辑器 Tab 切换 | 不占额外空间 |
| 2 | API 安全 | MVP 不做域名限制 | 快速验证优先 |
| 3 | 对话历史 | 会话级别，不持久化 | MVP 够用 |
| 4 | AI 参与度 | 每个操作都有 AI 路径 | 核心差异化 |
| 5 | 前端框架 | Vue 3 + Vite | 生态成熟 |
| 6 | 后端框架 | FastAPI | 异步、类型安全 |
| 7 | AI 模型 | Kimi (Moonshot API) | 用户已有 |
| 8 | 组件数量 | 15 个 | 覆盖常见场景 |
| 9 | Agent 拆分 | 4 个专精 Agent | 省 token |
| 10 | Command 系统 | AI 和手动操作输出同一种 JSON 指令 | 统一撤销/重做 |
| 11 | 导出方式 | 导出完整前后端项目 | 用户拿到就能跑 |
| 12 | 工作流 | 数据先行 + 设计先行两种模式并存 | 数据先行为推荐模式 |

---

## 两种工作模式

### 模式 A: 数据先行(推荐)

```
配置数据源(API/DB) → AI 看到真实数据 → AI 挑选合适图表 → 所见即所得 → 导出即可用
```

### 模式 B: 设计先行(原型/演示)

```
跳过数据配置 → AI 用 mock 数据设计 → 后续可连接真实数据 → 导出
```

### 用户入口

```
+----------------------------------------------+
|  AI 看板平台                                  |
|                                              |
|  [从数据开始] - 我已有 API 或数据库(推荐)      |
|  [从模板开始] - 我想先设计再连数据             |
|                                              |
|  已有项目:                                    |
|  > 电商销售看板    2026-04-23                 |
|  > 运营日报       2026-04-20                 |
+----------------------------------------------+
```

---

## AI 全程交互矩阵

| 操作 | 手动路径 | AI 路径 | 处理方式 |
|------|---------|---------|---------|
| 创建完整看板 | - | "做一个电商看板" | 场景 Agent (Kimi) |
| 添加组件 | 素材库拖拽 | "加一个订单量指标卡" | 组件 Agent (Kimi) |
| 修改组件 | 属性面板 | "标题改成XXX" | 组件 Agent (Kimi) |
| 删除/复制 | 右键菜单 | "删除这个" | 本地正则 (0 token) |
| 调整大小位置 | 拖拽 | "放大" "左移" | 本地正则 (0 token) |
| 调整布局 | 拖拽 | "两行三列" | 布局 Agent (Kimi) |
| 切换主题 | 主题选择器 | "暗色科技风" | 本地关键词 (0 token) |
| 接入数据源 | 表单填 API | "对接 /api/sales" | 数据 Agent (Kimi) + 后端探测 |

---

## 项目结构

```
digitalKanbanPlatform/
  frontend/
    src/
      core/
        command.js              # Command 基类 + execute/undo/redo
        registry.js             # 统一注册中心
        event-bus.js            # mitt 事件总线
      components/
        ProjectHome.vue         # 项目首页(新建/打开/选择模式) [新增]
        DataSourceSetup.vue     # 数据源配置页(API/DB 添加) [新增]
        AppLayout.vue           # 工作区整体布局骨架
        Workspace.vue           # 画布工作区
        MaterialLib.vue         # 左侧素材库
        RightPanel.vue          # 右侧面板(Tab: 属性|AI)
        PropEditor.vue          # 属性编辑器
        AiChat.vue              # AI 对话面板
        DataSourcePanel.vue     # 数据源管理(工作区内)
        ThemePicker.vue         # 主题切换
      widgets/
        _registry.js            # 组件注册表 + schema
        WidgetWrapper.vue       # 通用容器(选中/拖拽/缩放)
        KpiCard.vue / LineChart.vue / BarChart.vue / PieChart.vue
        DataTable.vue / TextBlock.vue
        NumberFlip.vue / ProgressRing.vue
        GaugeChart.vue / RadarChart.vue / ScatterChart.vue
        RankingList.vue / ClockWidget.vue
        MarqueeText.vue / BorderBox.vue
      ai/
        router.js               # 三层意图路由
        context.js              # 对话上下文(会话级)
        agents/
          _registry.js
          scene.js              # 场景 Agent(数据感知版)
          layout.js / component.js / data.js
      prompts/
        scene.md                # 场景 prompt(含数据源上下文) [重要变化]
        layout.md / component.md / data.md
      themes/
        _registry.js
        dark-tech.js / light-biz.js / cyber-neon.js
      stores/
        project.js              # 项目元数据(名称、数据源列表) [新增]
        dashboard.js            # 组件列表 + 选中态
        materials.js            # 素材库
        theme.js / datasource.js / history.js
      App.vue / main.js
    index.html / vite.config.js / package.json

  backend/
    app/
      main.py                   # FastAPI 入口 + CORS
      routers/
        ai.py                   # POST /api/ai/chat
        data.py                 # 数据源探测 + DB 连接 + 查询
        export.py               # POST /api/export/project
      agents/
        base.py / scene.py / layout.py / component.py / data.py
      services/
        kimi.py                 # Moonshot API 封装
        api_probe.py            # 探测 API 结构
        db_connector.py         # 数据库连接管理 [新增]
        query_executor.py       # 执行 SQL 查询 [新增]
        exporter.py             # 导出完整前后端项目
      export_templates/         # 导出模板
        server_template.py / requirements.txt
        README.md.j2 / API_DOCS.md.j2
      config.py
    requirements.txt
    .env

  README.md
```

---

## 核心数据结构

### Project(项目)

```javascript
{
  id: "proj_xxx",
  name: "电商销售看板",
  mode: "data-first",          // "data-first" | "design-first"
  dataSources: [               // 项目级数据源列表
    {
      id: "ds_1",
      name: "销售数据",
      type: "api",
      config: { url: "https://...", method: "GET", headers: {} },
      fields: ["date", "amount", "category"],  // 探测后填入
      sample: [...]                             // 示例数据
    },
    {
      id: "ds_2",
      name: "订单表",
      type: "database",
      config: { dialect: "mysql", host: "...", port: 3306, database: "..." },
      tables: ["orders", "products"],          // 连接后填入
      activeQuery: "SELECT ..."                // 当前查询
    }
  ],
  widgets: [...],              // 组件列表
  theme: "dark-tech",
  savedAt: "2026-04-23T..."
}
```

### Widget 实例

```javascript
{
  id: "widget_xxx",
  type: "kpi",
  props: { title: "今日订单", value: "1,234", trend: "up", unit: "单" },
  position: { x: 100, y: 50 },
  size: { w: 280, h: 160 },
  dataSource: {
    sourceId: "ds_1",           // 引用项目级数据源
    mapping: { value: "data.total", trend: "data.trend" },
    interval: 30000
  }
}
```

### Command 对象

```javascript
{
  type: "ADD_WIDGET",           // ADD | UPDATE | DELETE | MOVE | RESIZE | BATCH
  payload: { ... },
  undo: { ... },
  source: "ai"                  // "ai" | "manual"
}
```

### Agent 输出格式(统一)

```javascript
{
  "commands": [
    { "type": "ADD_WIDGET", "payload": { "type": "kpi", "props": {...} } }
  ],
  "message": "已添加 KPI 指标卡，数据来自销售 API"
}
```

---

## 场景 Agent Prompt 变化(数据先行的核心)

```markdown
# 前版 prompt(设计先行，AI 靠猜)
你是看板设计专家。用户需要: {{message}}
请生成组件列表。

# 新版 prompt(数据感知，AI 有依据)
你是看板设计专家。
用户需要: {{message}}
用户已有以下数据源:
{{#each dataSources}}
- {{name}}({{type}}): 字段 [{{fields}}], 示例 {{sample}}
{{/each}}

请根据数据源字段选择最合适的图表类型:
- 时间+数值 → 折线图
- 分类+数值 → 柱状图或饼图
- 单一数值 → KPI 卡
- 排名数据 → 排行榜

每个组件必须绑定一个真实数据源，指定 sourceId 和 mapping。
```

---

## 后端 API 契约

### POST /api/ai/chat
```
请求: { "message": "...", "context": { "widgets": [...], "dataSources": [...], "selectedId": "xxx" } }
响应: { "commands": [...], "message": "..." }
```

### POST /api/data/probe
```
请求: { "url": "...", "method": "GET", "headers": {} }
响应: { "status": 200, "fields": [...], "sample": [...], "structure": "..." }
```

### POST /api/data/db/connect
```
请求: { "dialect": "mysql", "host": "...", "port": 3306, "user": "...", "password": "...", "database": "..." }
响应: { "success": true, "tables": [{ "name": "orders", "columns": [...] }] }
```

### POST /api/data/db/query
```
请求: { "connectionId": "...", "sql": "SELECT ..." }
响应: { "columns": [...], "rows": [...], "rowCount": 100 }
```

### POST /api/export/project
```
请求: { "project": { widgets, dataSources, theme, title } }
响应: .zip 文件流
```

---

## 导出项目结构(用户下载解压后)

```
我的销售看板/
  frontend/
    index.html / css/dashboard.css / js/dashboard.js
  backend/
    server.py                  # FastAPI: 代理 API 或执行 SQL
    requirements.txt           # fastapi, uvicorn, pymysql(按需)
    data/                      # Mock 数据(备用)
    config.py                  # 数据源配置(API URL 或 DB 连接)
  API_DOCS.md                  # 每个接口的期望格式
  README.md                    # 使用 + 部署指南
  start.bat / start.sh         # 一键启动
```

---

## 15 个组件规格

| # | ID | 名称 | 分类 | ECharts | 默认尺寸 | 可配置属性 |
|---|-----|------|------|:---:|---------|-----------|
| 1 | kpi | KPI 指标卡 | 指标 | 否 | 280x160 | title, value, unit, trend, color |
| 2 | line | 折线图 | 图表 | 是 | 560x300 | title, series, xAxis, smooth, area |
| 3 | bar | 柱状图 | 图表 | 是 | 400x300 | title, series, xAxis, stack, horizontal |
| 4 | pie | 饼图 | 图表 | 是 | 300x300 | title, data, donut, showLabel |
| 5 | table | 数据表格 | 数据 | 否 | 500x320 | title, columns, rows, sortable |
| 6 | text | 标题文本 | 文本 | 否 | 400x80 | content, fontSize, align, color |
| 7 | number-flip | 数字翻牌 | 指标 | 否 | 260x140 | title, value, prefix, suffix, duration |
| 8 | progress | 进度环 | 指标 | 否 | 200x200 | title, percent, color, strokeWidth |
| 9 | gauge | 仪表盘 | 图表 | 是 | 300x280 | title, value, min, max, segments |
| 10 | radar | 雷达图 | 图表 | 是 | 350x320 | title, indicators, data |
| 11 | scatter | 散点图 | 图表 | 是 | 450x320 | title, data, xName, yName |
| 12 | ranking | 排行榜 | 数据 | 否 | 360x400 | title, items, showBar, maxItems |
| 13 | clock | 时钟 | 装饰 | 否 | 200x100 | format, showDate, timezone |
| 14 | marquee | 滚动字幕 | 文本 | 否 | 600x60 | text, speed, color |
| 15 | border-box | 装饰边框 | 装饰 | 否 | 400x300 | style, color, title, glowing |

---

## AI 意图路由规则

```
Level 1: 正则(0 token)
  /^(放大|缩小)/                → RESIZE_WIDGET
  /^(左移|右移|上移|下移)/       → MOVE_WIDGET
  /^删除/                       → DELETE_WIDGET
  /^复制/                       → DUPLICATE_WIDGET
  /^(标题|名称)(改|换)(成|为)(.+)/ → UPDATE_WIDGET

Level 2: 关键词(0 token)
  含"主题|风格|皮肤" + 已知主题名 → 切换主题
  含"对齐|居中|等距"              → 本地布局算法
  含"撤销|回退" / "重做|恢复"     → history

Level 3: Agent 路由(Kimi)
  含"看板|驾驶舱|大屏" 且无特指   → 场景 Agent
  含"加一个|添加|新增"            → 组件 Agent(create)
  含"改成|换成|修改"              → 组件 Agent(update)
  含"排列|布局|排版"              → 布局 Agent
  含"API|接口|数据|对接"          → 数据 Agent
  其他                            → Kimi 通用分类
```

---

## 3 套主题

| 主题 | 背景 | 面板 | 强调色 | 文字 |
|------|------|------|--------|------|
| dark-tech | #0a0e27 | #131837 | #00d4ff | #e0e6ff |
| light-biz | #f5f7fa | #ffffff | #1890ff | #333333 |
| cyber-neon | #0d0221 | #1a0a3e | #ff00ff/#00ffff | #ffffff |

---

## UI 布局

```
项目首页 → 数据源配置(可跳过) → 工作区

工作区:
+--------------------------------------------------+
|  顶栏: 项目名 | 主题切换 | 保存 | 导出 | 撤销/重做  |
+--------+--------------------+--------------------+
| 左侧栏  |    画布工作区       |  右侧栏            |
| 素材库   |    网格背景         |  [Tab: 属性|AI]    |
| 200px  |    自适应           |  300px              |
+--------+--------------------+--------------------+
```

---

## 分模块实施任务

### 模块 A: 项目脚手架

| 任务 | 操作 | 验收 |
|------|------|------|
| A1. Vue 3 + Vite 初始化 | npx create-vite | npm run dev 能跑 |
| A2. 安装依赖 | pinia, vue-echarts, echarts, mitt, nanoid | package.json 齐全 |
| A3. FastAPI 初始化 | backend/app/main.py + CORS | uvicorn 能跑 |
| A4. Vite 代理 | /api 代理到 localhost:8000 | 转发正常 |
| A5. 目录结构 | 创建所有目录 | 与规范一致 |

### 模块 B: 核心引擎

| 任务 | 关键文件 | 验收 |
|------|---------|------|
| B1. Command 系统 | core/command.js | execute / undo / redo |
| B2. 注册中心 | core/registry.js | registerWidget / registerAgent / registerTheme |
| B3. 事件总线 | core/event-bus.js | mitt |
| B4. Project Store | stores/project.js | 项目元数据 + 数据源列表 + 保存/加载 |
| B5. Dashboard Store | stores/dashboard.js | widgets CRUD + selectWidget |
| B6. History Store | stores/history.js | 与 Command 集成 |
| B7. Theme Store | stores/theme.js | applyTheme() |
| B8. DataSource Store | stores/datasource.js | 数据源绑定关系 |

### 模块 C: 15 个组件

| 任务 | 关键文件 | 验收 |
|------|---------|------|
| C1. WidgetWrapper | widgets/WidgetWrapper.vue | 选中 + 拖拽 + 缩放 |
| C2. 注册表 | widgets/_registry.js | 15 个 type->component/schema |
| C3-C17 | 各 .vue 文件 | 接收 props 渲染正确 |

### 模块 D: 工作区

| 任务 | 关键文件 | 验收 |
|------|---------|------|
| D1. 画布 | Workspace.vue | 1920x1080 + 网格 + 缩放 |
| D2. 拖拽移动 | WidgetWrapper | 更新 position |
| D3. 缩放手柄 | WidgetWrapper | 四角/四边 |
| D4. 选中 | Workspace | 蓝框 + 取消选中 |
| D5. 属性编辑 | PropEditor.vue | schema 驱动表单 |
| D6. 保存/恢复 | stores | localStorage |

### 模块 E: 项目管理 + 数据源配置 [新增模块]

| 任务 | 关键文件 | 验收 |
|------|---------|------|
| E1. 项目首页 | ProjectHome.vue | 新建(两种模式) + 打开已有项目 |
| E2. 数据源配置页 | DataSourceSetup.vue | 添加 API + 添加 DB |
| E3. API 探测 | api_probe.py + data.py | 输入 URL 返回字段+样本 |
| E4. DB 连接 | db_connector.py + data.py | 连接测试 + 列出表和字段 |
| E5. 项目保存/加载 | stores/project.js | localStorage 持久化项目列表 |

### 模块 F: 素材库

| 任务 | 关键文件 | 验收 |
|------|---------|------|
| F1. 素材列表 | MaterialLib.vue | 按分类显示 |
| F2. 搜索 | MaterialLib.vue | 关键词过滤 |
| F3. 拖拽添加 | MaterialLib -> Workspace | 创建实例 |

### 模块 G: AI 系统

| 任务 | 关键文件 | 验收 |
|------|---------|------|
| G1. 意图路由 | ai/router.js | 三层路由 |
| G2. 对话上下文 | ai/context.js | 会话级消息列表 |
| G3. Kimi 封装 | services/kimi.py | Moonshot API |
| G4. AI 路由接口 | routers/ai.py | POST /api/ai/chat |
| G5. 场景 Agent | agents/scene.py + prompts/scene.md | 数据感知版: 基于真实数据源选图表 |
| G6. 组件 Agent | agents/component.py | create/update/delete |
| G7. 布局 Agent | agents/layout.py | 位置调整 commands |
| G8. 数据 Agent | agents/data.py | API 探测 + DB AI 写 SQL + 字段映射 |
| G9. AI 对话面板 | AiChat.vue | 消息列表 + 输入 + AI 反馈 |

### 模块 H: 主题系统

| 任务 | 关键文件 | 验收 |
|------|---------|------|
| H1. CSS 变量 | themes/base.css | --bg, --panel, --accent |
| H2. 3 套预设 | dark-tech/light-biz/cyber-neon | 变量对象 |
| H3. 切换器 | ThemePicker.vue | UI + 自然语言 |

### 模块 I: 数据库数据源(增强)

| 任务 | 关键文件 | 验收 |
|------|---------|------|
| I1. SQL 执行 | query_executor.py | 执行查询返回结果 |
| I2. DB 查询接口 | routers/data.py | POST /api/data/db/query |
| I3. AI 写 SQL | 数据 Agent + prompt | 用户说需求 AI 生成 SQL |
| I4. 数据源面板 | DataSourcePanel.vue | 工作区内管理数据源 |

### 模块 J: 导出(全栈项目)

| 任务 | 关键文件 | 验收 |
|------|---------|------|
| J1. 导出模板 | export_templates/* | server_template + README + API_DOCS 模板 |
| J2. 前端生成 | exporter.py | widgets -> HTML/CSS/JS |
| J3. Mock 数据生成 | exporter.py | 从 props 提取示例 JSON |
| J4. 后端生成(API源) | exporter.py | 代理路由 |
| J5. 后端生成(DB源) | exporter.py | SQLAlchemy 查询路由 |
| J6. 文档生成 | exporter.py | README + API_DOCS |
| J7. 打包下载 | routers/export.py | zip 流 |
| J8. 启动脚本 | exporter.py | start.bat + start.sh |
| J9. JSON 导出 | 前端 | 导出配置文件 |

---

## 开发顺序(按验证优先级)

```
第一批 - 骨架(能看到东西):
  A(脚手架) -> B(核心引擎) -> C(前5个组件: kpi,line,bar,pie,text) -> D(工作区)
  里程碑: 画布上能拖拽、缩放、编辑 5 个组件

第二批 - 数据+AI(验证核心假设):
  E(项目管理+API数据源) -> G1-G5(AI路由+场景Agent) -> G9(AI面板)
  里程碑: 连接API -> AI基于真实数据生成看板 -> 看到真实数据
  *** 这是最关键的验证点: AI 基于真实数据生成的看板是否让用户满意 ***

第三批 - 补全体验:
  F(素材库) -> H(主题) -> G6-G8(其余Agent) -> C(剩余10个组件)
  里程碑: 完整的设计体验

第四批 - 数据库+导出:
  I(DB数据源+AI写SQL) -> J(全栈导出)
  里程碑: 连DB -> 导出完整项目 -> 解压即可运行

第五批 - 打磨(未来):
  问数功能 / 更多组件 / Docker导出 / 协作功能
```

---

## 验证计划

| 阶段 | 验证方式 |
|------|---------|
| 第一批完成 | 手动测试: 画布交互是否流畅 |
| 第二批完成 | 核心验证: 用免费API(天气/股票)测试AI生成看板质量 |
| 第三批完成 | 完整流程: 说话生成 -> 手动调整 -> 换主题 |
| 第四批完成 | 端到端: 连DB -> 设计 -> 导出 -> 部署 -> 浏览器查看 |
