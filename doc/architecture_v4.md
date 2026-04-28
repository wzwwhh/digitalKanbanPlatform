# AI 看板平台 - 前端架构规范 v4 (终版)

> 时间: 2026-04-24
> 目标: 一次重构到位，后续只加功能不改骨架

---

## 一、已确认的设计决策

| # | 决策 | 结论 |
|---|------|------|
| 1 | 导航风格 | 左侧固定侧边栏（可折叠） |
| 2 | 编辑器模式 | 全屏编辑，隐藏侧边栏，左上角"返回"按钮 |
| 3 | 工作台首页 | 最近看板 + 项目列表入口 + 新建项目 |
| 4 | 智能问数 | 预留菜单入口，后续再设计 |
| 5 | 数据与设计 | **不是二选一，是混合交叉的过程**（核心变化） |
| 6 | 数据源管理 | 项目下的独立页面，随时可进可出 |
| 7 | **AI 定位** | **AI-First：AI 能做用户能做的一切，是全方位参与者** |

---

## 一(补)、AI-First 设计原则

> **核心定位：AI 不是辅助工具，是全方位参与的核心能力。用户能手动做的每一件事，AI 都必须能做。**

### AI 完整能力矩阵

| 操作类型 | 手动方式 | AI 方式（自然语言） | Command 类型 |
|---------|---------|-------------------|-------------|
| 添加组件 | 从组件面板点击/拖拽 | "加一个折线图" | ADD_WIDGET |
| 删除组件 | 选中 → 删除按钮 | "删掉这个" | DELETE_WIDGET |
| 移动组件 | 拖拽 | "把这个移到右上角" | MOVE_WIDGET |
| 缩放组件 | 四角手柄 | "放大一倍" "宽度设为500" | RESIZE_WIDGET |
| 改标题 | 属性面板输入 | "标题改成月度销售" | UPDATE_WIDGET |
| 改颜色 | 属性面板选色 | "颜色换成红色" "用蓝色系" | UPDATE_WIDGET |
| 改字号 | 属性面板滑块 | "字号调大" "标题用36号字" | UPDATE_WIDGET |
| 改数据 | 属性面板编辑 | "数据改成1月到6月" | UPDATE_WIDGET |
| 切换图表类型 | 无（需删除重建） | "这个换成柱状图" | DELETE + ADD |
| **绑定数据源** | 属性面板选择数据源 | "用销售API的数据" | UPDATE_WIDGET |
| **解绑数据源** | 属性面板清空 | "这个改回用假数据" | UPDATE_WIDGET |
| **改数据映射** | 属性面板选字段 | "X轴用日期，Y轴用销售额" | UPDATE_WIDGET |
| 批量操作 | 无 | "所有卡片颜色改成蓝色" | BATCH |
| 整体风格 | 主题切换 | "暗色科技风" | CHANGE_THEME |
| 生成整体看板 | 无 | "做一个电商看板" | BATCH(多个ADD) |
| **基于数据补充** | 无 | "从销售API里再挑几个合适的图表" | BATCH(多个ADD) |
| 撤销/重做 | 按钮 | "撤销" "恢复" | UNDO/REDO |

### 组件级数据源绑定

每个组件可以单独绑定一个数据源，并指定字段映射：

```
选中一个折线图 → 属性面板 → 数据源 Tab:
┌──────────────────────────────────┐
│ 数据源: [销售API ▼] (可选/可清空) │
│                                  │
│ 字段映射:                         │
│   X轴: [date ▼]                  │
│   Y轴: [amount ▼]                │
│   系列: [category ▼] (可选)       │
│                                  │
│ 刷新间隔: [30] 秒 (0=不刷新)      │
└──────────────────────────────────┘
```

AI 也能通过自然语言完成同样操作：
- "这个折线图用销售API的数据，X轴是date，Y轴是amount"
- → 解析为 UPDATE_WIDGET { dataSource: { sourceId, mapping: { x, y } } }

### AI 上下文设计

每次 AI 对话发送到后端时，上下文必须包含：

```javascript
context = {
  // 画布上所有组件（AI 知道"已有什么"）
  widgets: [{ id, type, props, position, size, dataSource }],
  // 当前选中的组件（AI 知道"用户在说哪个"）
  selectedId: "widget_xxx" | null,
  // 项目所有数据源（AI 知道"有什么数据可用"）
  dataSources: [{ id, name, type, fields, sample }],
  // 当前主题
  theme: "dark-tech"
}
```

这样 AI 才能做出有依据的决策，比如：
- 用户说"加个图表" → AI 看到有销售API，自动选折线图并绑定
- 用户说"颜色换掉" → AI 看到选中了一个 KPI 卡，修改它的 color 属性
- 用户说"再补充几个" → AI 看到已有4个KPI但没有图表，补充折线图和饼图

---

## 二、"混合工作流"设计（核心变化）

### 之前的设计（错误）
```
选模式(二选一) → 配数据 OR 直接画 → 编辑 → 导出
```
问题：把用户锁死在一条路径上，不灵活。

### 新设计（正确）
```
创建看板 → 进入编辑器 → 随时做以下任何事（不分先后，可反复）:
  ├── 手动从组件面板拖一个图表进来
  ├── 对AI说"加一个KPI卡"
  ├── 去数据源页面配一个API
  ├── 回来对AI说"用刚才那个API的数据做个折线图"
  ├── 手动调整位置和样式
  ├── 对AI说"再从数据里挑几个合适的图表补充一下"
  └── 继续手动微调 → 满意 → 导出
```

**关键原则**：
- 画布始终是真实状态，AI 和手动操作都是往画布上**叠加**，不会相互覆盖
- 数据源可以在编辑过程中随时添加，不是前置步骤
- AI 能感知"画布上已有什么 + 有哪些数据源"，做增量补充而非全量覆盖

### 对编辑器的影响
- 编辑器顶栏增加"数据源"快捷入口（弹出抽屉或小面板，不离开编辑器）
- AI 对话面板的 prompt 需要包含当前画布状态 + 所有已配数据源
- SceneAgent 改为"增量模式"：在现有组件基础上补充，而非清空重建

---

## 三、完整路由结构

```
/                                   → 工作台（最近编辑 + 快速入口）
/projects                           → 项目列表
/project/:id                        → 项目概览（重定向到看板列表）
/project/:id/dashboards             → 看板列表（卡片形式）
/project/:id/datasources            → 数据源管理（增删改查）
/project/:id/ask                    → 智能问数（预留，显示"开发中"）
/project/:id/settings               → 项目设置（名称、默认主题、导出配置）
/project/:id/dashboard/:did/edit    → 看板编辑器（全屏模式）
/project/:id/dashboard/:did/preview → 看板预览（全屏无边框展示）
```

---

## 四、页面布局

### 4.1 App Shell（除编辑器外的所有页面）

```
┌─ 顶栏 ─────────────────────────────────────────┐
│  🎯 AI看板平台    [当前项目名 ▼]    [新建项目]   │
├─ 侧边栏 ──┬─ 内容区 ──────────────────────────┤
│  (项目内)  │                                    │
│  📊 看板   │   （根据路由渲染对应页面）           │
│  🔗 数据源 │                                    │
│  🤖 问数   │                                    │
│  ⚙️ 设置  │                                    │
│            │                                    │
│ ─────────  │                                    │
│  (全局)    │                                    │
│  🏠 工作台 │                                    │
│  📁 项目   │                                    │
└────────────┴────────────────────────────────────┘
```

侧边栏分两段：上半部分是当前项目的功能菜单，下半部分是全局入口。
未选中项目时，只显示全局部分。

### 4.2 看板编辑器（全屏模式）

```
┌─ 编辑器顶栏 ───────────────────────────────────────────────┐
│ ← 返回  |  看板名称  |  [数据源⚡] [主题🎨] [撤销↩] [重做↪] [保存💾] [导出📦]  │
├─ 组件面板 ─┬─ 画布 ──────────────────┬─ 右侧面板 ──────────┤
│  搜索...   │                         │ [属性] [AI助手]      │
│  📊 指标   │    1920×1080            │                      │
│  📈 图表   │    网格画布              │  属性编辑 / AI对话   │
│  📝 文本   │                         │                      │
│  🎨 装饰   │                         │                      │
├────────────┴─────────────────────────┴──────────────────────┤
│ 状态栏: 组件数 8 | 数据源 2 已连接 | 上次保存 14:30          │
└─────────────────────────────────────────────────────────────┘
```

**与现在的区别**：
- 顶栏增加"← 返回"（回到项目页）和"数据源⚡"快捷按钮
- 左侧组件面板增加搜索和分类折叠
- 底部增加状态栏（可选）
- 侧边栏导航在编辑器中隐藏

### 4.3 "数据源⚡"按钮的交互

点击后弹出右侧抽屉面板（不离开编辑器）：
```
┌─ 数据源管理 ──────────────────┐
│                               │
│  已添加 (2)                    │
│  ┌───────────────────────┐   │
│  │ 🔗 销售API  [5字段]  ✕ │   │
│  │ 🔗 用户API  [3字段]  ✕ │   │
│  └───────────────────────┘   │
│                               │
│  ＋ 添加 API 数据源            │
│  ＋ 添加数据库连接             │
│                               │
│  ─────────────────────────── │
│  API地址: [________________]  │
│  方式: [GET ▼]                │
│  [🔍 探测字段]                │
│                               │
└───────────────────────────────┘
```

这样数据源管理既有独立页面（项目侧边栏），也有编辑器内的快捷入口。

---

## 五、数据模型变化

### 现在
```javascript
Project = { id, name, mode, dataSources[], widgets[], theme }
// 项目和看板是 1:1，组件没有数据源绑定
```

### 重构后
```javascript
Project = {
  id, name, theme,
  dataSources: [],       // 项目级共享，所有看板都能引用
}

Dashboard = {
  id, projectId, name,
  widgets: [],           // 每个看板自己的组件列表
  createdAt, savedAt,
}

// Widget 实例（增加 dataSource 绑定）
Widget = {
  id, type,
  props: { title, value, color, fontSize, ... },  // 所有属性 AI 都能改
  position: { x, y },     // AI 能改（"移到右上角"）
  size: { w, h },          // AI 能改（"放大一倍"）
  dataSource: {            // 组件级数据源绑定（可选）
    sourceId: "ds_1",      // 引用项目级数据源
    mapping: {             // 字段映射
      x: "date",           // X轴字段
      y: "amount",         // Y轴字段
      series: "category",  // 系列字段（可选）
      value: "total",      // KPI 取值字段
    },
    interval: 30000,       // 自动刷新间隔(ms)，0=不刷新
  }
}
// 项目和看板是 1:N，每个组件可独立绑定数据源
```

### Store 变化
```
projectStore  → 管理项目列表 + 当前项目 + 数据源
dashboardStore → 管理当前项目的看板列表 + 当前编辑的看板 + widgets
historyStore  → 不变（但 scope 限定为当前看板）
themeStore    → 不变
```

---

## 五(补)、预览模式

编辑器顶栏加 **👁 预览** 按钮，点击后进入 `/project/:id/dashboard/:did/preview`。

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│              纯净全屏看板展示                          │
│              无编辑器边框/面板                         │
│              数据源按 interval 自动刷新                │
│                                                     │
│                        [ESC 返回编辑] (浮动按钮)      │
└─────────────────────────────────────────────────────┘
```

**与导出的区别**：
- 预览 = 在应用内全屏展示，数据实时刷新，随时可回到编辑
- 导出 = 生成独立 HTML 文件，脱离应用运行

---

## 五(补2)、数据运行时流转

组件绑定数据源后，数据的获取和渲染链路：

```
前端 DataFetcher 服务 (新建 services/data-fetcher.js)
│
├── 编辑模式: 绑定时 fetch 一次 → 用真实数据替换 mock → 不自动刷新
├── 预览模式: 按 widget.dataSource.interval 定时 fetch → 自动更新图表
└── 导出 HTML: 把 fetch 逻辑写进 <script> → 浏览器端直接请求 API
```

**DataFetcher 职责**：
1. 根据 `widget.dataSource.sourceId` 找到项目数据源的 URL/Method/Headers
2. 发 HTTP 请求拿到原始 JSON
3. 根据 `widget.dataSource.mapping` 把原始数据转成组件需要的 props 格式
4. 返回转换后的数据，由组件自行渲染

```javascript
// services/data-fetcher.js
export async function fetchWidgetData(widget, dataSources) {
  const ds = dataSources.find(d => d.id === widget.dataSource?.sourceId)
  if (!ds) return null
  const raw = await fetch(ds.config.url, { method: ds.config.method, headers: ds.config.headers })
  const json = await raw.json()
  return applyMapping(json, widget.dataSource.mapping, widget.type)
}
```

---

## 五(补3)、新建看板引导

用户在看板列表点"新建看板"时，弹出轻量对话框：

```
┌─ 新建看板 ─────────────────────────────────┐
│                                             │
│  看板名称: [________________]               │
│                                             │
│  如何开始:                                   │
│  ○ 空白画布 — 自己拖组件搭建                 │
│  ○ AI 生成 — 描述你想要的看板                │
│     [做一个销售数据大屏___________]          │
│  ○ 从模板选择（敬请期待）                    │
│                                             │
│              [取消]  [创建]                 │
└─────────────────────────────────────────────┘
```

选 "AI 生成" → 进入编辑器后自动触发 AI 对话 → 生成初始布局 → 用户继续混合工作流调整。
这样"从模板/从AI"不再是全局二选一，而是新建看板时的一个轻引导。

---

## 六、前瞻性检查：还有哪些坑？

### ✅ 已考虑：数据持久化迁移
现在用 localStorage，将来可能要换成后端数据库。
**应对**: Store 的 save/load 方法设计为可替换的"持久化适配器"，现在用 localStorage 实现，将来换成 API 调用只需替换适配器，不动业务逻辑。

```javascript
// stores/persistence.js
export const persistence = {
  save(key, data) { localStorage.setItem(key, JSON.stringify(data)) },
  load(key) { return JSON.parse(localStorage.getItem(key)) },
}
// 将来换成:
// save(key, data) { return fetch('/api/save', { body: data }) }
```

### ✅ 已考虑：组件版本兼容
用户保存的项目里记录了 widget schema，如果我们更新组件代码，旧项目可能不兼容。
**应对**: _registry.js 里给每个组件加 `version` 字段，加载旧项目时做 migration。

### ✅ 已考虑：实时数据刷新
看板查看模式（非编辑模式）需要定时拉取 API 数据更新图表。
**应对**: Widget 的 props 里有 `dataSource.interval` 字段（已设计但未实现），编辑器里不刷新，导出后/预览模式下启用轮询。

### ✅ 已考虑：多人协作（远期）
如果将来要加协作，需要操作同步。
**应对**: Command 系统天然适合 OT/CRDT，每个操作都是序列化的 JSON 命令，可以通过 WebSocket 广播。当前不实现，但架构不阻碍。

### ✅ 已考虑：权限（远期）
项目可能需要分享给别人看（只读）。
**应对**: 路由设计已预留 `/project/:id/settings`，将来可以在这里加权限配置。导出的 HTML 天然就是只读的。

### ✅ 已考虑：模板/素材市场（远期）
用户可能想保存某个看板配置为模板，或分享给其他人。
**应对**: 侧边栏可以加"模板"菜单项。Dashboard 的 JSON 结构本身就是可序列化的模板。

---

## 七、实施计划

### Phase 1: App Shell + 路由骨架
- 安装 vue-router
- 创建 AppShell.vue（顶栏 + 侧边栏 + router-view）
- 创建 SideNav.vue（侧边导航组件）
- 创建 WorkspacePage.vue（工作台首页）
- 创建 ProjectListPage.vue
- 配置路由表（含所有页面路由）
- App.vue 改为 router-view
- 现有 ProjectHome.vue 废弃

### Phase 2: 项目-看板层级改造
- projectStore 扩展（多项目 + 项目级数据源）
- dashboardStore 重构（多看板 + 当前看板）
- 创建 DashboardListPage.vue（看板列表，卡片式 + 新建看板对话框）
- 创建 ProjectSettingsPage.vue
- 持久化适配器 persistence.js

### Phase 3: 编辑器全屏化
- AppLayout.vue → EditorLayout.vue（纯编辑器布局）
- 增加"← 返回"按钮 + "👁 预览"按钮 + "数据源⚡"抽屉
- 左侧组件面板增加搜索和分类折叠
- PropEditor 拆分为 [样式] [数据] 两个子 Tab
- 底部状态栏

### Phase 4: 数据源管理 + 组件绑定
- 创建 DataSourcePage.vue（项目级独立页面）
- 创建 DataSourceDrawer.vue（编辑器内抽屉，复用核心逻辑）
- PropEditor 数据 Tab：数据源选择 + 字段映射 + 刷新间隔
- 数据源增删可在两个入口操作，Store 同步

### Phase 5: 预览模式 + 数据流转
- 创建 DashboardPreviewPage.vue（全屏无边框展示）
- 创建 services/data-fetcher.js（数据获取+映射服务）
- 编辑模式：绑定时 fetch 一次，用真实数据渲染
- 预览模式：按 interval 定时刷新
- 导出 HTML 嵌入 fetch 逻辑

### Phase 6: 混合工作流 + AI 增强
- SceneAgent 改为增量模式（感知已有组件，做补充而非覆盖）
- AI 上下文包含完整 widgets + dataSources + selectedId
- AI 可执行所有 18 种操作（能力矩阵全覆盖）
- 新建看板时支持"AI 生成"选项
- AI 上下文压缩（精简发送内容，控制 token）

---

## 八、文件变化清单

### 新建文件
```
frontend/src/
  router/
    index.js                    # 路由配置
  layouts/
    AppShell.vue                # 应用外壳（顶栏+侧边栏+router-view）
    EditorLayout.vue            # 编辑器全屏布局（从 AppLayout 演化）
  pages/
    WorkspacePage.vue           # 工作台首页
    ProjectListPage.vue         # 项目列表
    DashboardListPage.vue       # 看板列表 + 新建看板对话框
    DashboardEditorPage.vue     # 看板编辑器入口（包裹 Workspace）
    DashboardPreviewPage.vue    # 看板预览（全屏无边框）
    DataSourcePage.vue          # 数据源管理（项目内）
    AskPage.vue                 # 智能问数（预留）
    ProjectSettingsPage.vue     # 项目设置
  components/
    SideNav.vue                 # 侧边导航
    DataSourceDrawer.vue        # 编辑器内数据源抽屉
    NewDashboardDialog.vue      # 新建看板对话框（空白/AI生成/模板）
  services/
    data-fetcher.js             # 数据获取 + 字段映射
    persistence.js              # 持久化适配器（localStorage → API）
```

### 改造文件
```
App.vue               → 改为只包含 router-view
AppLayout.vue          → 改名为 EditorLayout.vue，去掉外壳部分
ProjectHome.vue        → 废弃，功能迁移到 WorkspacePage + ProjectListPage
DataSourceConfig.vue   → 拆分为页面版 + 抽屉版，共享核心逻辑
PropEditor.vue         → 拆分为 [样式] [数据] 两个子 Tab
projectStore           → 扩展支持多项目、项目级数据源
dashboardStore         → 增加多看板管理 + currentDashboard
```

### 不变的文件（直接复用）
```
core/command.js, registry.js, event-bus.js
widgets/ 全部 16 个组件 + WidgetWrapper.vue
stores/history.js, theme.js, datasource.js, materials.js
components/Workspace.vue, AiChat.vue, ThemePicker.vue
后端所有代码
```

---

## 九、注意事项

1. **AI 上下文压缩**: 发给 Kimi 时只发 type/props/dataSource，不发 position/size（除非用户在问布局）
2. **PropEditor 拆分**: 属性面板分 [样式] [数据] 两个子Tab，样式改 props，数据选数据源+映射
3. **组件版本**: _registry.js 加 version 字段，加载旧项目时做 migration
4. **持久化适配器**: persistence.js 统一 save/load 接口，当前 localStorage 实现
