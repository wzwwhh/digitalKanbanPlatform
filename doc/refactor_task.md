# 前端架构重构 - 任务追踪

> 基于 architecture_v4.md

---

## Phase 1: App Shell + 路由骨架 ✅

- `[x]` 安装 vue-router@4
- `[x]` 创建 router/index.js（完整路由表）
- `[x]` 创建 layouts/AppShell.vue（顶栏 + 侧边栏 + router-view）
- `[x]` 创建 components/SideNav.vue（项目内菜单 + 全局菜单）
- `[x]` 创建 pages/WorkspacePage.vue（工作台首页）
- `[x]` 创建 pages/ProjectListPage.vue（项目列表）
- `[x]` 创建 pages/DashboardListPage.vue（看板列表 + 新建对话框）
- `[x]` 创建 pages/DashboardEditorPage.vue（编辑器入口）
- `[x]` 创建 pages/DashboardPreviewPage.vue（预览占位）
- `[x]` 创建 pages/DataSourcePage.vue（数据源占位）
- `[x]` 创建 pages/AskPage.vue（问数占位）
- `[x]` 创建 pages/ProjectSettingsPage.vue（设置占位）
- `[x]` App.vue 改为 router-view + 全局样式
- `[x]` main.js 挂载 router

## Phase 2: 项目-看板层级改造 ✅

- `[x]` projectStore 扩展（多项目 + 多看板 CRUD + 自动加载）
- `[x]` 持久化适配器 services/persistence.js
- `[x]` projectStore 迁移到 persistence 适配器
- `[x]` DashboardListPage 看板卡片显示组件数
- `[x]` 编辑器保存时写入看板级 widgets（非项目级）
- `[x]` 编辑器加载时读取对应看板的 widgets
- `[x]` 编辑器顶栏：← 返回按钮 + 看板名称
- `[x]` 工作台最近编辑：只显示已保存的看板，正确排序

## MVP Sprint: 数据链路打通 ✅

- `[x]` 后端 mock_data 路由（4个模拟数据接口）
- `[x]` DataSourcePage 完整实现（探测 + 保存 + Mock 快捷通道）
- `[x]` services/dataFetcher.js（数据获取 + dataPath 提取）
- `[x]` LineChart/BarChart/PieChart/KpiCard 接入 dataFetcher
- `[x]` SceneAgent 数据感知 prompt（含 sourceId + 字段映射）
- `[x]` AiChat 上下文含 dataSource
- `[x]` CHANGE_THEME 只改看板不改系统

## Phase 3: 编辑器增强 ✅

- `[x]` PropEditor 拆分 [样式] [数据] 两个子 Tab
- `[x]` 数据 Tab: 数据源下拉 + 字段映射选择器（根据组件类型动态）
- `[x]` 增加 "⚡数据源" 快捷抽屉
- `[x]` 增加 "👁 预览" 按钮 → 路由到预览
- `[x]` 左侧组件面板搜索 + 分类折叠
- `[x]` DashboardPreviewPage 完整实现（全屏 + 缩放 + ESC）
- `[x]` 路由名统一 (editor → dashboard-edit, preview → dashboard-preview)

## Phase 6 核心: AI 增量 + 体验 ✅

- `[x]` SceneAgent 增量模式 prompt（不覆盖已有组件）
- `[x]` base.py 上下文含 pos/size/ds
- `[x]` AI 路由增强（增量/绑定/解绑关键词）
- `[x]` ComponentAgent 支持 7 种组件 + dataSource
- `[x]` 新建看板"AI 生成"自动触发对话
- `[x]` AiChat 智能快捷按钮（感知数据源+组件状态）
- `[x]` AI 上下文含 theme

## 代码清理 ✅

- `[x]` 删除 ProjectHome.vue（死代码）
- `[x]` 删除 DataSourceConfig.vue（死代码）
- `[x]` 修复 WorkspacePage 日期排序 bug
- `[x]` 修复 AppLayout 编辑器高度 bug（100% → 100vh）
- `[x]` 修复 SceneAgent 缺少 dataSource ID
- `[x]` 修复 AiChat context 漏 dataSource
- `[x]` 修复 base.py 缩进错误

---

## ✅ 全部已完成

### Phase 4: 看板主题 ✅
- `[x]` 5 个内置主题（暗色科技/商务亮色/赛博霓虹/极简白/森林绿）
- `[x]` 注册中心驱动（新增主题零修改核心代码）
- `[x]` 色板预览（Settings 页颜色圆点 + ThemePicker 自定义下拉）
- `[x]` 导出主题感知（后端 5 主题调色板同步）
- `[x]` 自定义主题创建（颜色选择器 + 实时预览 + 保存应用）
- `[x]` 主题库持久化（localStorage 保存/加载/删除 + registry 动态注册）
- `[x]` ThemePicker 联动（自定义主题显示名称而非 ID）

### Phase 5: 预览 + 导出增强 ✅
- `[x]` 导出 HTML 嵌入 fetch 逻辑（动态数据 30s 刷新）
- `[x]` 前端传递 dataSources 到导出接口
- `[ ]` 导出 ZIP + 启动脚本（可选扩展）

### Phase 6 剩余: AI 能力矩阵 ✅
- `[x]` AI 批量修改（"所有卡片颜色改红色" → BATCH 命令）
- `[x]` AI 切换图表类型（"换成柱状图" → UPDATE_WIDGET type 字段）
- `[x]` AI 上下文压缩（精简 token）
- `[x]` 9 种颜色关键词映射 + 12 种图表类型关键词
- `[x]` 新增极简/森林 2 套主题关键词

### Phase 7: 智能问数 ✅
- `[x]` AskPage 完整对话式 UI
- `[x]` 数据源选择器
- `[x]` 关键词 → 图表类型推荐
- `[x]` 快捷问题建议按钮
- `[x]` 后端 /api/ai/ask 端点

### 编辑器增强 ✅
- `[x]` 快捷键帮助面板 (ShortcutsHelp.vue)
- `[x]` ? 键打开/关闭帮助
- `[x]` 预览页全屏切换 (F 键)
- `[x]` 预览页显示看板名+组件数

### AI 意图精度加固 ✅
- `[x]` 双重验证机制（触发词 + 操作目标 都要匹配）
- `[x]` 撤销/重做精确匹配（短消息 ≤6 字 + startsWith）
- `[x]` 颜色关键词去重叠（单字"绿""白"不再与主题冲突）
- `[x]` 图表切换三重验证（选中 + 触发词 + 图表类型名）
- `[x]` 模糊指令 LLM 兜底（"主题推荐一下" → 不误触，交 LLM）
- `[x]` test_ai_intent.py 测试脚本 11/11 通过

### 组件补全 ✅
- `[x]` RankingList 接入 dataFetcher + 进度条
- `[x]` DataTable 接入 dataFetcher + 自动列检测
- `[x]` NumberFlip 翻牌动画 + dataFetcher
- `[x]` ProgressRing SVG 弧形 + 自动变色
- `[x]` ClockWidget 实时更新（修复 bug）
- `[x]` MarqueeText 完整滚动
- `[x]` BorderBox 四角装饰 + 发光

### AI 质量 ✅
- `[x]` Prompt 精准化（ranking/table mapping）
- `[x]` Context 压缩（去 props，12 个截断）
- `[x]` JSON 解析三层 fallback
- `[x]` ComponentAgent 选中约束

### 快捷键 ✅
- `[x]` Ctrl+S 保存
- `[x]` Ctrl+D 复制组件
- `[x]` Delete/Backspace 删除组件
- `[x]` Ctrl+Z/Y 撤销重做

### 画布交互 ✅
- `[x]` 滚轮缩放
- `[x]` 右键菜单（复制/置顶/删除）
- `[x]` 缩放感知拖拽（dx/scale）
- `[x]` Toast 浮动通知（替代 alert）

### 导航增强 ✅
- `[x]` 全局对话框 composable（替代 prompt/confirm）
- `[x]` 面包屑导航（三级）
- `[x]` 页面过渡动画
- `[x]` 工作台统计概览
- `[x]` 最近看板显示所有（不限 savedAt）
- `[x]` 设置页危险区域 + 删除项目
- `[x]` updateProjectName 公共 API
