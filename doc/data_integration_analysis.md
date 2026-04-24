# AI 看板平台 - 真实数据接入与生产化讨论

## 你提出的核心问题

> 用户手里有 API 或数据库，如何让导出的项目就是能直接部署使用的？

这把产品定位从**"看板设计工具"**提升到了**"看板生产系统"**。区别很大：

| | 设计工具 | 生产系统 |
|--|---------|---------|
| 设计时数据 | Mock 假数据 | 真实业务数据 |
| 导出产物 | 需要二次开发才能用 | 直接部署就能用 |
| 用户价值 | 省了画 UI 的时间 | 省了整个开发过程 |
| 竞争壁垒 | 低（很多人能做） | 高（几乎没人这么做） |

**我的判断：生产系统方向更有价值，而且技术上完全可行。**

---

## 竞品都在做什么？（差距在哪）

| 产品 | 连真实数据 | AI 辅助 | 导出独立项目 | 定位 |
|------|:---:|:---:|:---:|------|
| Grafana | Yes | No | No(只导出 JSON 快照) | 监控仪表板，需要持续运行 Grafana |
| Metabase | Yes | 部分(自然语言查询) | No | BI 工具，需要持续运行 Metabase |
| Superset | Yes | No | No | 企业 BI，运维成本高 |
| DataV | Yes | No | No | 阿里云绑定 |
| Appsmith | Yes | Yes | No(自托管但不导出代码) | 内部工具平台 |
| Lovable | No(需自行接) | Yes | Yes(导出 React 代码) | 通用 Web 应用 |
| **我们** | **Yes** | **Yes** | **Yes** | **AI 看板生产系统** |

关键发现：**没有一个产品同时做到"连真实数据 + AI 辅助 + 导出独立项目"**。

- Grafana/Metabase 能连数据但不能导出独立项目（你必须一直运行它们）
- Lovable 能导出代码但不专注数据看板
- 我们的定位是：**用 AI 帮你连接数据、设计看板、然后导出一个完全独立的项目**

---

## 完整用户场景走一遍

### 场景：某电商运营需要一个销售数据看板

```
Step 1: 用户打开平台
  → "帮我做一个电商销售看板"
  → AI 场景 Agent 生成布局(KPI卡+折线图+饼图+排行榜)
  → 画布上出现看板，数据是 AI 预填的示例数据

Step 2: 用户连接真实数据
  方式 A - 有 API:
    → "这个折线图对接 https://my-server.com/api/v1/sales"
    → 后端探测 API，返回字段结构
    → AI 数据 Agent 自动映射: date->x轴, amount->y轴
    → 折线图立即显示真实数据

  方式 B - 有数据库:
    → 用户在数据源面板填写: MySQL / host:port / user / password / database
    → 后端连接数据库，列出所有表
    → 用户说"用 orders 表做趋势图"
    → AI 生成 SQL: SELECT DATE(created_at) as date, SUM(amount) as total FROM orders GROUP BY date
    → 折线图显示真实数据

  方式 C - 手动配置:
    → 用户在数据源面板手动填 URL、选字段映射
    → 不需要 AI，纯表单操作

Step 3: 用户调整看板
  → "把主题换成暗色" → 主题切换
  → "指标卡显示今日/昨日/本月三个" → AI 添加组件
  → 手动拖拽微调位置

Step 4: 导出
  → 点击导出
  → 下载 zip，包含:
     - 前端: 看板页面
     - 后端: server.py，已配置好 API 代理或 DB 查询
     - 文档: API 格式说明 + 部署指南
  → 解压，python server.py，浏览器打开就是生产看板
```

---

## 技术可行性分析

### 1. API 数据源（简单，可先做）

```
用户输入: API URL + Method + Headers(可选) + Auth(可选)
平台做:
  1. 后端代理请求该 API → 拿到返回数据
  2. 分析 JSON 结构 → 提取字段列表
  3. AI 建议字段映射 或 用户手动选择
  4. 前端组件通过平台后端代理获取数据

导出时:
  - server.py 中生成对应的代理路由
  - 或直接在前端 JS 中请求该 API(如果跨域允许)
  - config.py 中存放 API URL，方便修改

技术难度: ★★☆☆☆ (简单，就是 HTTP 代理)
```

### 2. 数据库数据源（中等，第二步做）

```
用户输入: 数据库类型 + 连接信息 + SQL 查询(或 AI 帮写)
平台做:
  1. 后端通过 SQLAlchemy 连接数据库
  2. 列出 tables/columns 供用户选择
  3. AI 根据表结构和用户需求生成 SQL
  4. 执行查询，返回数据给前端组件

导出时:
  - server.py 中包含 SQLAlchemy 连接代码
  - 每个 API 路由执行对应的 SQL 查询
  - config.py 中存放 DB 连接信息(带注释)
  - requirements.txt 加入 pymysql / psycopg2

技术难度: ★★★☆☆ (中等，SQLAlchemy 生态成熟)
支持的数据库(MVP): MySQL, PostgreSQL, SQLite
```

### 3. AI 写 SQL（加分项，锦上添花）

```
用户: "用 orders 表做一个按月的销售趋势"
AI 数据 Agent:
  → 先查表结构: orders(id, amount, created_at, status, ...)
  → 生成 SQL: SELECT DATE_FORMAT(created_at, '%Y-%m') as month,
              SUM(amount) as total FROM orders
              WHERE status='completed' GROUP BY month ORDER BY month
  → 用户确认或修改
  → 执行查询，映射到折线图

技术难度: ★★★☆☆ (Kimi 写 SQL 能力很强，给好 schema 即可)
```

---

## 架构层面需要什么变化

### 数据源类型扩展

```javascript
// 现有设计
dataSource: {
  type: "static" | "api",
  ...
}

// 扩展后
dataSource: {
  type: "static" | "api" | "database",

  // type="api" 时
  url: "https://...",
  method: "GET",
  headers: {},
  auth: { type: "bearer", token: "xxx" },
  mapping: { value: "data.total" },
  interval: 30000,

  // type="database" 时
  connectionId: "conn_xxx",    // 引用 datasource store 中的连接
  query: "SELECT ... FROM ...",
  mapping: { value: "total" },
  interval: 60000
}
```

### 新增后端服务

```
backend/services/
  api_probe.py       # 已有: 探测 API 结构
  db_connector.py    # 新增: 数据库连接管理
  query_executor.py  # 新增: 执行 SQL 并返回结果
```

### 新增/修改后端路由

```
POST /api/data/probe          # 已有: 探测 API
POST /api/data/db/connect     # 新增: 测试数据库连接
POST /api/data/db/tables      # 新增: 列出表和字段
POST /api/data/db/query       # 新增: 执行 SQL 查询
POST /api/data/db/ai-query    # 新增: AI 根据需求生成 SQL
GET  /api/data/fetch/:sourceId # 新增: 统一数据获取(代理 API 或执行 SQL)
```

### 导出器增强

```
exporter.py 需要根据数据源类型生成不同的 server.py:
  - API 数据源 → 生成代理路由(httpx 转发)
  - DB 数据源 → 生成 SQLAlchemy 查询路由
  - 混合 → 两种都有
  - requirements.txt 动态添加 pymysql/psycopg2
```

---

## MVP 安全策略

| 关注点 | MVP 方案 | 理由 |
|--------|---------|------|
| DB 密码存储 | 会话级内存，不持久化 | 安全优先，用户每次重新输入 |
| 导出时凭据 | config.py 中写占位符 + 注释 | 不把真实密码打包进 zip |
| API Key | 同上 | 导出的 config.py 有 YOUR_API_KEY_HERE |
| SQL 注入 | 参数化查询 | SQLAlchemy 默认防注入 |
| 网络访问 | 后端代理所有外部请求 | 前端不直接连 DB/API |

---

## 我的专家建议

### 1. 分步实现，价值递增

```
Phase 1 (当前 MVP): API 数据源 + Mock 导出
  → 用户能连 API，设计时看真实数据，导出带代理后端
  → 已经比大多数竞品强了

Phase 2: 数据库数据源
  → 支持 MySQL/PostgreSQL/SQLite
  → AI 帮写 SQL
  → 导出带 DB 查询的后端

Phase 3: 智能化增强
  → AI 根据数据自动推荐图表类型
  → AI 检测数据异常自动建议告警
  → 定时刷新配置
```

### 2. 这个方向的先进性

当前市场格局：
- **Grafana/Metabase**: 能连数据，但你必须永远运行它们的平台
- **Lovable/v0.dev**: 能导出代码，但不专注数据连接
- **我们的独特价值**: 连接真实数据 + AI 设计 + 导出独立项目 = **"用完即走"的看板工厂**

这个"用完即走"非常关键：用户不需要永远依赖我们的平台，导出后就是自己的东西。这反而会降低用户的决策门槛（"试试又不会被绑定"）。

### 3. 对实施计划的影响

需要在现有计划中调整的：
- **模块 H（数据源）扩大**: 从只有 API 探测变成 API + DB 完整数据源管理
- **数据 Agent 增强**: 能理解表结构、写 SQL
- **模块 I（导出）增强**: 根据数据源类型动态生成后端代码
- **新增统一数据层**: 前端组件不关心数据从哪来（API/DB/静态），统一通过一个 fetch 接口获取

### 4. 建议的开发顺序调整

```
原第三批: H(数据源) → F8(数据Agent) → C(补全组件)
改为:
  第三批-A: H(API数据源+探测+实时预览)
  第三批-B: H(DB数据源+连接+AI写SQL)
  第三批-C: F8(数据Agent增强) → C(补全组件)

原第四批: I(导出)
改为:
  第四批: I(全栈导出，根据数据源类型生成不同后端)
```

---

## 需要你确认

1. **MVP 先做 API 还是 DB？** 我建议先做 API（更简单，场景更普遍），DB 放第二步
2. **DB 支持哪些？** 我建议 MVP 先 MySQL + PostgreSQL + SQLite
3. **AI 写 SQL 放 MVP 吗？** 我建议放，因为这是核心差异化（Kimi 写 SQL 能力很强）
4. **这个方向你认同吗？** "用完即走的看板工厂" 这个定位
