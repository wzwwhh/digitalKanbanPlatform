# AI 看板平台 - 项目现状总览

> **最后更新**: 2026-04-27 (全 Phase 完成 + 深度审计)
> **项目目录**: `digitalKanbanPlatform/`
> **架构规范**: `doc/architecture_v4.md`
> **定位**: AI-First 看板生产平台 — "连上数据，说句话，导出来直接部署"

---

## 一、项目简介

AI 驱动的数据可视化看板平台。支持多项目、多看板管理，用户可以通过自然语言描述需求，AI 自动生成完整看板，也可以手动拖拽编辑。支持对接真实 API 数据源，最终导出为可独立部署的 HTML 文件。

### 核心能力
1. **多项目多看板** — 项目 → 看板 1:N 层级管理
2. **AI 一句话生成看板** — 输入"做一个电商看板"，AI 自动生成布局
3. **数据源管理** — 可添加 API 数据源，自动探测字段结构（含内置模拟数据）
4. **数据驱动生成** — AI 基于真实数据源字段，选择合适的图表并自动绑定数据
5. **组件实时数据** — 图表组件可绑定数据源，从真实 API 获取数据渲染
6. **混合工作流** — AI 生成和手动编辑可交替进行，互不覆盖
7. **手动精调** — 所有组件可拖拽、缩放、编辑属性
8. **一键导出** — 导出为单文件 HTML，引入 ECharts CDN
9. **智能问数** — 自然语言提问，AI 推荐合适的可视化方式
10. **自定义主题** — 5 内置 + 无限自定义主题，颜色选择器实时预览

---

## 二、技术栈

| 层 | 技术 | 说明 |
|---|------|------|
| 前端框架 | Vue 3 + Vite 8 | SFC 组件 + HMR |
| 路由 | vue-router 4 | App Shell + 多页面 |
| 状态管理 | Pinia | 6 个 Store |
| 图表库 | ECharts 5 + vue-echarts | 5 类图表组件 |
| 后端 | FastAPI (Python) | 异步 + 类型安全 |
| AI 模型 | Kimi (Moonshot API) | 兼容 OpenAI SDK |
| 通信 | Vite Proxy → FastAPI | 开发环境 /api 转发 |

---

## 三、当前架构

```
用户 → App Shell (顶栏+侧边栏) → 页面路由
                                   ├── 工作台 (最近编辑 + 统计概览)
                                   ├── 项目列表 (创建/删除/进入)
                                   ├── 看板列表 (新建对话框 + AI/空白模式)
                                   ├── 数据源管理 ✅ (探测+保存+内置Mock)
                                   ├── 智能问数 ✅ (AI 对话式分析 + 图表推荐)
                                   └── 项目设置 ✅ (5 主题+自定义主题+项目删除)

       编辑器 (全屏独立路由) ← ← ← ← 点击看板卡片进入
       ├── 左侧: 素材库 (15 个组件, 4 分类)
       ├── 中间: 画布 (拖拽/缩放/右键菜单)
       └── 右侧: 属性面板 / AI 助手 (三层意图路由)

       预览 (全屏独立路由，占位) ← ← 编辑器顶栏预览按钮
```

### 数据链路（MVP 核心）

```
数据源管理页:
  用户选 Mock/输入URL → 后端 api_probe → 返回 fields/sample → 存入 projectStore

编辑器 AI 对话:
  用户说需求 → AiChat 携带 dataSources 上下文 → 后端 SceneAgent
  → AI 根据字段选图表 + 绑定 sourceId/mapping
  → 前端 executeCommand(ADD_WIDGET) → 组件 onMounted → dataFetcher
  → fetch 真实 API → 按 mapping 提取 → 渲染真实数据
```

---

## 四、项目进度

### ✅ 已完成

| 阶段 | 内容 | 状态 |
|------|------|------|
| MVP | 脚手架、核心引擎、15个组件、画布、属性编辑 | ✅ |
| MVP | AI 对话、3层意图路由、Kimi 封装、导出 HTML | ✅ |
| MVP | 数据源配置、API 探测服务 | ✅ |
| Phase 1 | App Shell + vue-router + 侧边导航 + 10条路由 | ✅ |
| Phase 2 | 多项目多看板 CRUD + 看板级持久化 + 持久化适配器 | ✅ |
| 代码清理 | 删除死代码 + props Bug 修复 + 主题解耦 | ✅ |
| MVP Sprint | Mock API + 数据源管理页 + dataFetcher + AI 数据绑定 | ✅ |
| Phase 3 | PropEditor 样式/数据 Tab + 编辑器工具栏 + 组件搜索/分类 + 预览页 | ✅ |
| Phase 6 (核心) | AI 增量模式 + 数据绑定路由 + 上下文增强 (pos/size/ds) | ✅ |
| AI 体验 | 新建看板 AI 自动触发 + 智能快捷按钮 + RankingList/DataTable 数据接入 | ✅ |
| AI 质量 | Prompt 精准化 + Context 压缩 + JSON 解析增强 + ranking/table mapping | ✅ |
| Phase 5 | 导出 HTML 含动态数据刷新 (30s interval) + dataSources 传递 | ✅ |
| 组件增强 | ClockWidget 实时 + ProgressRing SVG + NumberFlip 翻牌 + GaugeChart ECharts | ✅ |
| 交互优化 | 右键菜单 + 滚轮缩放 + Ctrl+D 复制 + Toast 通知 + 缩放感知拖拽 | ✅ |
| 导航增强 | 面包屑 + 全局对话框 + 页面过渡动画 + 工作台统计 + 设置页危险区 | ✅ |
| **Phase 4 核心** | **5 主题 + 色板预览 + 注册中心驱动 + 导出主题感知** | **✅** |
| **Phase 7** | **智能问数页面 + 关键词图表推荐 + 数据源选择 + 对话式交互** | **✅** |
| **编辑器增强** | **快捷键帮助面板 (?) + 预览全屏 (F) + 看板名/组件数** | **✅** |
| **Phase 6 AI** | **批量颜色修改 + 图表类型切换 + 9 色/12 图表关键词 + 5 主题关键词** | **✅** |
| **Phase 4 完整** | **自定义主题创建/保存/删除 + 颜色选择器 + 持久化 + ThemePicker 联动** | **✅** |
| **AI 精度加固** | **意图双重验证 + 置信度守卫 + 模糊指令 LLM 兜底 + 11/11 测试通过** | **✅** |

### 🎉 全部核心 Phase 已完成

> 无剩余必做项，仅保留扩展可能（更多组件类型、更多 AI Agent 等）

---

## 五、项目文件结构

```
digitalKanbanPlatform/
├── doc/                              # 项目文档
│   ├── STATUS.md                     # ← 本文件
│   ├── architecture_v4.md            # 架构规范 (最新版)
│   ├── TESTING.md                    # 测试指南
│   └── ...                           # 其他分析文档
│
├── frontend/                         # Vue 3 前端
│   ├── src/
│   │   ├── App.vue                   # router-view + 全局 CSS
│   │   ├── main.js                   # 挂载 pinia + router
│   │   ├── router/
│   │   │   └── index.js              #   路由配置 (10条)
│   │   ├── layouts/
│   │   │   └── AppShell.vue          #   应用外壳
│   │   ├── pages/                    #   页面组件 (8个)
│   │   │   ├── WorkspacePage.vue     #   工作台首页
│   │   │   ├── ProjectListPage.vue   #   项目列表
│   │   │   ├── DashboardListPage.vue #   看板列表 + 新建对话框
│   │   │   ├── DashboardEditorPage.vue # 编辑器入口
│   │   │   ├── DashboardPreviewPage.vue # 预览 (占位)
│   │   │   ├── DataSourcePage.vue    #   数据源管理 ✅
│   │   │   ├── AskPage.vue           #   智能问数 (占位)
│   │   │   └── ProjectSettingsPage.vue # 设置 (占位)
│   │   ├── components/               #   业务组件
│   │   │   ├── AppLayout.vue         #   编辑器布局
│   │   │   ├── SideNav.vue           #   侧边导航
│   │   │   ├── Workspace.vue         #   画布区域
│   │   │   ├── PropEditor.vue        #   属性面板
│   │   │   ├── AiChat.vue            #   AI 对话
│   │   │   └── ThemePicker.vue       #   主题选择
│   │   ├── services/
│   │   │   ├── persistence.js        #   持久化适配器
│   │   │   └── dataFetcher.js        #   数据获取服务 ✅ (NEW)
│   │   ├── stores/                   #   Pinia 状态管理 (6个)
│   │   ├── core/                     #   命令系统
│   │   ├── widgets/                  #   16 个可视化组件
│   │   └── themes/                   #   3 套主题预设
│   └── vite.config.js
│
├── backend/                          # FastAPI 后端
│   ├── app/
│   │   ├── main.py                   #   入口 + CORS
│   │   ├── config.py                 #   配置
│   │   ├── routers/
│   │   │   ├── ai.py                 #   AI 三层路由
│   │   │   ├── data.py               #   数据源探测/连接
│   │   │   ├── export.py             #   HTML 导出
│   │   │   └── mock_data.py          #   模拟数据 API ✅ (NEW)
│   │   ├── agents/
│   │   │   ├── base.py               #   Agent 基类
│   │   │   ├── scene.py              #   场景 Agent (数据感知)
│   │   │   └── component.py          #   组件 Agent (数据感知)
│   │   └── services/
│   │       ├── kimi.py               #   Kimi API 封装
│   │       ├── api_probe.py          #   API 探测 (支持相对路径)
│   │       └── db_connector.py       #   数据库连接
│   ├── requirements.txt
│   └── .env
│
└── .gitignore
```

---

## 六、启动方式

```bash
# 前端
cd frontend && npm install && npm run dev

# 后端
cd backend && pip install -r requirements.txt
# 配置 .env: MOONSHOT_API_KEY=sk-xxx
python -m uvicorn app.main:app --port 8000 --reload
```

---

## 七、关键设计决策

1. **App Shell 架构**: 顶栏+侧边栏+router-view，编辑器独立全屏路由
2. **项目→看板 1:N**: 一个项目包含多个看板，每个看板独立管理组件
3. **Command 模式统一操作**: AI 和手动操作输出同一种 JSON 指令
4. **混合工作流**: AI 生成和手动编辑不互斥，可交替进行
5. **三层路由省 Token**: 简单操作正则/关键词本地处理，复杂需求才调 LLM
6. **持久化适配器**: 统一 save/load 接口，当前 localStorage 将来可换 API
7. **Schema 驱动属性编辑**: 组件注册表定义 schema，PropEditor 自动生成表单
8. **组件级数据绑定**: 每个 widget 可独立绑定数据源 + 字段映射，由 dataFetcher 运行时获取
9. **AI CHANGE_THEME 只改看板**: 系统主题和看板风格解耦，AI 操作只影响看板
10. **Mock API 自包含**: 内置模拟数据端点，不依赖外部网络即可完整演示
