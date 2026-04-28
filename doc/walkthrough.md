# 里程碑：Phase 1-2 完成 — App Shell + 多看板架构

> 完成日期: 2026-04-25
> 基于: architecture_v4.md

---

## 完成内容

### Phase 1: App Shell + 路由骨架 ✅

| 文件 | 类型 | 说明 |
|------|------|------|
| `router/index.js` | 新建 | 完整路由表（10 条路由，含嵌套和独立路由） |
| `layouts/AppShell.vue` | 新建 | 应用外壳：顶栏 + 可折叠侧边栏 + router-view |
| `components/SideNav.vue` | 新建 | 侧边导航（项目菜单 + 全局菜单，router-link 自动高亮） |
| `pages/WorkspacePage.vue` | 新建 | 工作台首页（最近编辑 + 快速入口） |
| `pages/ProjectListPage.vue` | 新建 | 项目列表（卡片式，显示看板/数据源数量） |
| `pages/DashboardListPage.vue` | 新建 | 看板列表 + 新建看板对话框（空白/AI生成/模板三选一） |
| `pages/DashboardEditorPage.vue` | 新建 | 编辑器入口，传递路由参数给 AppLayout |
| `pages/DashboardPreviewPage.vue` | 新建 | 预览页占位 |
| `pages/DataSourcePage.vue` | 新建 | 数据源管理占位 |
| `pages/AskPage.vue` | 新建 | 智能问数占位 |
| `pages/ProjectSettingsPage.vue` | 新建 | 项目设置占位 |
| `App.vue` | 改造 | 精简为 `<router-view>` + 全局 CSS 变量 |
| `main.js` | 改造 | 挂载 vue-router |

### Phase 2: 多看板层级 + 持久化 ✅

| 文件 | 类型 | 说明 |
|------|------|------|
| `stores/project.js` | 改造 | 多项目 + 多看板 CRUD，自动加载，`persistence` 适配器 |
| `services/persistence.js` | 新建 | 持久化适配器（当前 localStorage，将来可换 API） |
| `components/AppLayout.vue` | 改造 | 接收 projectId/dashboardId props，看板级保存/加载 |

### 代码清理

| 文件 | 动作 | 原因 |
|------|------|------|
| `components/ProjectHome.vue` | 🗑️ 删除 | 旧首页，功能已迁移到路由页面 |
| `components/DataSourceConfig.vue` | 🗑️ 删除 | 无任何引用 |
| `doc/architecture_discussion.md` | 🗑️ 删除 | 已被 `architecture_v4.md` 取代 |

### Bug 修复

| 问题 | 修复 |
|------|------|
| `WorkspacePage` 日期排序错误（ISO 字符串不能做数字减法） | 改用 `localeCompare` |
| `WorkspacePage` 显示未保存的看板 | 只显示 `savedAt` 不为空的 |
| `AppLayout` 编辑器高度不够 | `height: 100%` → `100vh`（编辑器是独立路由，不在 AppShell 内） |

---

## 验证结果

所有页面和流程验证通过：

- ✅ 工作台首页：欢迎区 + 最近编辑卡片
- ✅ 项目列表：卡片显示看板/数据源数量
- ✅ 看板列表：卡片显示组件数 + 新建对话框
- ✅ 编辑器：← 返回按钮 + 看板名称 + 全屏编辑
- ✅ 占位页面：数据源/问数/设置 均正确显示
- ✅ 数据持久化：保存→返回→重新打开，widgets 完整保留
- ✅ 路由导航：侧边栏菜单切换流畅，高亮正确

---

## 当前文件结构

```
frontend/src/
├── App.vue                    # router-view + 全局样式
├── main.js                    # 挂载 pinia + router
├── router/
│   └── index.js               # 路由配置
├── layouts/
│   └── AppShell.vue           # 应用外壳
├── pages/
│   ├── WorkspacePage.vue      # 工作台
│   ├── ProjectListPage.vue    # 项目列表
│   ├── DashboardListPage.vue  # 看板列表 + 新建对话框
│   ├── DashboardEditorPage.vue # 编辑器入口
│   ├── DashboardPreviewPage.vue # 预览（占位）
│   ├── DataSourcePage.vue     # 数据源（占位）
│   ├── AskPage.vue            # 问数（占位）
│   └── ProjectSettingsPage.vue # 设置（占位）
├── components/
│   ├── AppLayout.vue          # 编辑器布局（Phase 3 改为 EditorLayout）
│   ├── SideNav.vue            # 侧边导航
│   ├── Workspace.vue          # 画布
│   ├── PropEditor.vue         # 属性面板
│   ├── AiChat.vue             # AI 对话
│   └── ThemePicker.vue        # 主题选择
├── services/
│   └── persistence.js         # 持久化适配器
├── stores/
│   ├── project.js             # 项目 + 看板管理
│   ├── dashboard.js           # 画布组件状态
│   ├── history.js             # 撤销/重做
│   ├── theme.js               # 主题
│   ├── datasource.js          # 数据源
│   └── materials.js           # 素材
├── core/                      # 命令系统
├── widgets/                   # 16 个组件
└── themes/                    # 主题注册
```

---

## Phase 3 编辑器增强 ✅ (2026-04-25)

- PropEditor 拆分 [样式] + [数据] 双 Tab
- 编辑器顶栏: ⚡数据源抽屉 + 👁预览按钮
- 组件面板: 搜索 + 分类折叠 (指标/图表/文本/数据/装饰)
- 预览页全屏渲染 + 自适应缩放 + ESC 返回
- 路由名统一: dashboard-edit / dashboard-preview

## AI 体验增强 ✅ (2026-04-26)

- 新建看板选"AI 生成" → 进编辑器自动触发 AI 对话
- AI 快捷按钮感知数据源/组件状态，动态推荐不同操作
- AI 增量模式（不覆盖已有组件，放在空白区域）
- RankingList/DataTable 接入 dataFetcher

## 下一步

- Phase 4: 看板主题独立编辑
- Phase 5: 预览数据刷新 + 导出含 fetch
- Phase 6 剩余: AI 批量修改能力

