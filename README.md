# 🎯 AI 看板平台 (Digital Kanban Platform)

> **连上数据，说句话，导出来直接部署**

AI 驱动的数据可视化看板平台。通过自然语言描述需求，一句话生成完整看板；支持手动拖拽精调、实时数据绑定、一键导出独立 HTML。

---

## ✨ 项目亮点

| 特性 | 说明 |
|------|------|
| 🤖 **AI 一句话生成** | 输入"做一个电商销售看板"，AI 自动生成完整布局 |
| 🎯 **三层意图路由** | 正则(0 token) → 关键词(0 token) → LLM Agent，精准匹配不浪费 |
| 📊 **15 种可视组件** | 折线/柱状/饼图/仪表盘/雷达/散点/排行榜/数据表格/翻牌器/进度环等 |
| 🔗 **真实数据绑定** | 对接 API 数据源，自动探测字段，图表实时刷新 |
| 🎨 **5+N 主题系统** | 5 内置主题 + 自定义主题创建/保存，颜色选择器实时预览 |
| 📦 **一键导出 HTML** | 单文件可独立部署，内嵌数据轮询 30s 自动刷新 |
| ↩️ **撤销/重做** | 完整 Command 系统，AI 操作和手动操作统一可撤销 |
| 💬 **智能问数** | 自然语言提问数据，AI 推荐可视化方式 |

## 🏗️ 技术栈

```
前端: Vue 3 + Vite 8 + Pinia + ECharts 5 + vue-echarts
后端: FastAPI (Python) + Kimi (Moonshot AI)
通信: Vite Proxy → FastAPI (/api)
持久化: localStorage (前端) + .env (后端)
```

## 🚀 快速启动

```bash
# 前端
cd frontend
npm install
npm run dev            # → http://localhost:5173

# 后端
cd backend
pip install -r requirements.txt
# 配置 AI (可选，不配也能用批量操作/主题切换)
echo "MOONSHOT_API_KEY=你的Key" > .env
python -m uvicorn app.main:app --port 8000 --reload
```

## 📁 项目结构

```
digitalKanbanPlatform/
├── frontend/                # Vue 3 前端
│   └── src/
│       ├── components/      # 核心组件 (AppLayout, AiChat, Workspace...)
│       ├── pages/           # 页面 (工作台/项目/看板/数据源/问数/设置)
│       ├── widgets/         # 15 个可视化组件 + 注册中心
│       ├── stores/          # 6 个 Pinia Store
│       ├── themes/          # 5 个内置主题
│       └── core/            # 注册中心 + Command 系统 + 事件总线
├── backend/                 # FastAPI 后端
│   └── app/
│       ├── routers/         # AI/导出/数据源/Mock 路由
│       ├── agents/          # Scene/Component Agent (Kimi)
│       └── services/        # Kimi SDK 封装
└── doc/                     # 项目文档 (11 个文件)
```

## 🎮 核心流程

```
1. 新建项目 → 添加数据源 (或使用内置 Mock)
2. 新建看板 → 选择"AI 生成"
3. AI 对话: "做一个电商销售看板" → 自动布局
4. 手动精调: 拖拽/缩放/属性编辑
5. 预览 → 导出 HTML → 部署
```

## 🧠 AI 架构

```
用户消息 → Level 1 正则 (0 token, 精确命令)
         → Level 2 关键词 (0 token, 主题/颜色/图表/撤销)
         → Level 3 LLM Agent (Kimi, 场景生成/组件修改)
```

**设计原则**: 宁可漏过交 LLM，不可误触做错事

## 📄 License

MIT
