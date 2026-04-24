# AI 看板平台 - 阶段总结

## 第一批: 骨架与核心交互 ✅
- Vue 3 + Vite 前端架构，FastAPI 后端提供代理。
- **Command 系统** (支持操作历史记录：撤销/重做)
- 实现了注册中心，管理 widget, agent, theme, datasource 的动态扩展。
- 5个可用的标准图表组件，附带 Schema 驱动的属性编辑器。
- 可拖拽缩放的无界画布（1920x1080）。

## 第二批: 数据接入与 AI 助手 ✅

### 数据源探针接入 (Data Source & API Probe)
1. **探针服务 (`api_probe.py`)**: 后端实现了动态调用第三方 API 接口，并能解析返回 JSON 结构的逻辑。如果返回对象内包含数组、直接返回数组，探针都能提取字段名和获取示例数据 (Sample)。
2. **可视化配置页面 (`DataSourceConfig.vue`)**: 新建"从数据开始"的项目时，会先进入配置界面。用户输入 API 并点击"探测字段"，系统自动解析出字段列表。确认后存储到项目中。

### AI 多层意图路由系统 (AI Chat & Routing)
1. **前端交互面板 (`AiChat.vue`)**: 用户可以在右侧的 AI 助手中直接发号施令，例如“做一个电商看板”或快捷按钮。包含了加载中（思考动画）和返回结果处理逻辑。
2. **多层路由架构 (`routers/ai.py`)**:
    - **Level 1 (正则匹配，0 Token 消耗)**: 识别“删除选中”、“左移50”、“标题改成XXX”等指令，直接返回对用的 Frontend Commands。
    - **Level 2 (关键词匹配，0 Token 消耗)**: 识别“切换暗色主题”、“撤销操作”等常用控制动作。
    - **Level 3 (AI 大模型处理)**: 如果无法在前端直接解决，路由会将指令分配给指定的 Agent。
3. **分场景 Agent (`SceneAgent` & `ComponentAgent`)**:
    - `ComponentAgent`: 负责独立组件维度的增删改。
    - `SceneAgent`: 复杂需求生成。系统会将用户绑定的数据源的 **字段与样例信息** 与用户请求共同拼接，发送给 Kimi / Moonshot API 协助生成整体布局的 Command JSON，达到真实的“数据感知”。

## 下一步建议 (模块 I & J)
1. **打包与导出**: 生成用户可以直接用来部署的纯净代码 (打包 HTML 或 Vite 工程)。
2. **直连数据库**: 后续补充针对 MySQL/PG 的连接探针逻辑。

> [!TIP]
> 平台需要填写 `MOONSHOT_API_KEY` 在 `backend/.env` 中才能激活真实的 LLM 能力。
