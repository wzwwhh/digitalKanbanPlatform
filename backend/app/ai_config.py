"""
AI 能力中控 — 统一管理所有 AI 配置

所有 AI 相关的常量、规则、映射、配置集中在这里，
ai.py 和各 Agent 从这里导入，避免分散在多个文件中。

AI 文件索引:
├── ai_config.py        ← 本文件：统一配置中心
├── routers/ai.py       ← 三层意图路由 + API 端点
├── agents/base.py      ← Agent 基类 (context 序列化)
├── agents/scene.py     ← Scene Agent (生成完整看板)
├── agents/component.py ← Component Agent (单组件操作)
└── services/kimi.py    ← Kimi (Moonshot) API 封装
"""

# ========== Level 1: 正则规则 ==========

REGEX_RULES = [
    # (正则模式, 动作标识)
    # 删除选中
    (r"^删除(这个|当前|选中)?$", "DELETE_SELECTED"),
    # 复制选中
    (r"^复制(这个|当前|选中)?$", "DUPLICATE_SELECTED"),
    # 方向移动 (左移/右移/上移/下移 + 可选数值)
    (r"^(左移|右移|上移|下移)(\d+)?$", "MOVE_DIRECTION"),
    # 缩放 (放大/缩小 + 可选数值)
    (r"^(放大|缩小)(\d+)?$", "RESIZE_DIRECTION"),
    # 标题修改
    (r"^(?:标题|名称)(?:改|换)(?:成|为)(.+)$", "RENAME_TITLE"),
]

# ========== Level 2: 关键词映射 ==========

# 主题名称 → 主题 ID
THEME_KEYWORDS = {
    "暗色": "dark-tech", "深色": "dark-tech", "科技": "dark-tech", "科技蓝": "dark-tech",
    "亮色": "light-biz", "浅色": "light-biz", "商务": "light-biz",
    "霓虹": "cyber-neon", "赛博": "cyber-neon", "炫酷": "cyber-neon",
    "极简": "minimal-white", "简洁": "minimal-white", "极简白": "minimal-white",
    "森林": "forest-green", "自然": "forest-green", "森林绿": "forest-green",
}

# 颜色名称 → HEX
COLOR_MAP = {
    "红色": "#ff4560", "红": "#ff4560",
    "蓝色": "#00d4ff", "蓝": "#00d4ff",
    "绿色": "#00e396",
    "紫色": "#7b61ff", "紫": "#7b61ff",
    "橙色": "#feb019", "橙": "#feb019",
    "黄色": "#ffd700", "黄": "#ffd700",
    "白色": "#ffffff",
    "粉色": "#ff69b4", "粉": "#ff69b4",
    "青色": "#00ffff", "青": "#00ffff",
}

# 图表类型名称 → 组件 type
CHART_TYPE_MAP = {
    "折线图": "line", "折线": "line", "曲线图": "line",
    "柱状图": "bar", "柱图": "bar", "柱形图": "bar", "条形图": "bar",
    "饼图": "pie", "饼状图": "pie", "环形图": "pie",
}

# 触发词
THEME_TRIGGERS = ["主题", "风格", "皮肤"]
COLOR_TRIGGERS = ["颜色改", "改颜色", "颜色换", "换颜色", "颜色变", "改成颜色"]
CHART_TRIGGERS = ["换成", "改成", "变成", "切换为", "切换成"]

# ========== Level 3: Agent 路由关键词 ==========

# 消息包含以下关键词 → 使用 Scene Agent
SCENE_KEYWORDS = ["看板", "驾驶舱", "大屏", "面板", "仪表板"]
SCENE_INCREMENT_KEYWORDS = ["补充", "再加几个", "再补", "再做", "继续补", "帮我完善"]

# 消息包含以下关键词 → 使用 Layout Agent
LAYOUT_KEYWORDS = [
    "排版", "布局", "排列", "对齐", "整理", "重新排版", "自动布局",
    "排一下", "排好", "摆整齐",
    # 位置调整类（自然语言定位）
    "放在", "放到", "移到", "挪到", "摆到", "放右", "放左",
    "左上角", "右上角", "左下角", "右下角", "居中", "中间",
]

# 消息包含以下关键词 → 使用 Component Agent
COMPONENT_ADD_KEYWORDS = ["加一个", "添加", "新增", "创建"]
COMPONENT_EDIT_KEYWORDS = ["改成", "换成", "修改", "更新", "调整"]
COMPONENT_DATA_KEYWORDS = ["绑定", "数据源", "用这个数据", "X轴", "Y轴", "映射"]
COMPONENT_UNBIND_KEYWORDS = ["解绑", "假数据", "取消绑定"]

# ========== 智能问数: 关键词 → 图表推荐 ==========

CHART_SUGGESTIONS = {
    "趋势": "line", "变化": "line", "增长": "line", "走势": "line",
    "占比": "pie", "比例": "pie", "分布": "pie", "构成": "pie",
    "对比": "bar", "比较": "bar", "排名": "bar", "排行": "bar",
    "最高": "bar", "最低": "bar", "最大": "bar", "最多": "bar",
    "前几": "bar", "Top": "bar",
}

# ========== 安全限制 ==========

# 正则操作的数值上限
MAX_MOVE_DISTANCE = 500     # 移动最大像素
MAX_RESIZE_AMOUNT = 500     # 缩放最大像素
MAX_WIDGET_WIDTH = 1920     # 组件最大宽度
MAX_WIDGET_HEIGHT = 1080    # 组件最大高度
MIN_WIDGET_WIDTH = 80       # 组件最小宽度
MIN_WIDGET_HEIGHT = 60      # 组件最小高度

# ========== 可用组件类型 (Agent prompt 用) ==========

AVAILABLE_WIDGET_TYPES = [
    "text", "kpi", "line", "bar", "pie", "ranking", "table",
    "gauge", "radar", "scatter", "number-flip", "progress",
    "clock", "marquee", "border-box", "map", "echarts-custom",
]

# ========== Level 3: LLM 意图分类 ==========

# 分析/对话类关键词（不操作画布，纯文本回答）
ANALYSIS_KEYWORDS = [
    "分析", "解读", "洞察", "总结", "说明", "解释",
    "怎么样", "什么情况", "为什么", "原因", "建议",
    "预测", "趋势如何", "有什么问题",
]

# 背景色触发词
BACKGROUND_TRIGGERS = ["背景色", "背景", "底色", "画布颜色", "画布背景"]

# LLM 意图分类 prompt（花约 30 token 准确分类，避免关键词误判）
INTENT_CLASSIFY_PROMPT = """判断用户意图，只返回一个JSON对象：{"intent":"类型"}
类型只能是以下之一：
- "scene": 要生成/补充整个看板（如"做一个电商看板""补充几个图表"）
- "component": 要添加/修改/删除单个组件（如"加一个饼图""把标题改成红色"）
- "layout": 要排版/对齐/调整布局（如"排版""对齐""整理一下"）
- "analysis": 要分析数据/解读图表/提问题（如"分析一下""趋势怎么样"）
- "chat": 闲聊/建议/询问/不确定（如"有什么建议""你觉得呢"）

用户说: "{message}"
"""
