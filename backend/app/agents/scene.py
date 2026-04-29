"""
场景 Agent - 根据用户需求 + 数据源信息，一次性生成完整看板布局

这是最重要的 Agent，数据感知版：
- 如果有数据源：根据真实字段选择合适的图表
- 如果没有数据源：根据常识生成 mock 数据
"""
import json
from app.agents.base import BaseAgent
from app.services.kimi import chat_completion_json

SCENE_SYSTEM_PROMPT = """你是一个专业的数据看板设计专家。根据用户的需求，生成一个完整的看板布局。

你必须返回一个 JSON 对象，格式如下：
{
  "commands": [
    {
      "type": "ADD_WIDGET",
      "payload": {
        "type": "组件类型",
        "props": { "属性键值对" },
        "position": { "x": 数字, "y": 数字 },
        "size": { "w": 数字, "h": 数字 },
        "dataSource": { "sourceId": "数据源ID", "mapping": { "字段映射" }, "sql": "查询SQL" }
      }
    }
  ],
  "message": "描述你做了什么的中文说明"
}

可用组件类型和属性：
1. text - 标题文本: {content, fontSize(默认24), align(left/center/right), color}
2. kpi - KPI指标卡: {title, value, unit, trend(up/down/flat), color}
   - 数据绑定: dataSource.mapping = { "value": "字段名" }
3. line - 折线图: {title, smooth(布尔), area(布尔)}
   - 数据绑定: dataSource.mapping = { "x": "X轴字段名", "y": "Y轴字段名" }
4. bar - 柱状图: {title, stack(布尔), horizontal(布尔)}
   - 数据绑定: dataSource.mapping = { "x": "X轴字段名", "y": "Y轴字段名" }
5. pie - 饼图: {title, donut(布尔), showLabel(布尔)}
   - 数据绑定: dataSource.mapping = { "name": "名称字段", "value": "数值字段" }
6. ranking - 排行榜: {title, showBar(布尔), maxItems(默认10)}
   - 数据绑定: dataSource.mapping = { "name": "名称字段", "value": "数值字段" }
7. table - 数据表格: {title, sortable(布尔)}
   - 数据绑定: dataSource.mapping = { "name": "名称字段", "value": "数值字段" }
8. gauge - 仪表盘: {title, value(数字), min(默认0), max(默认100)}
9. radar - 雷达图: {title}
10. scatter - 散点图: {title, xName, yName}
11. number-flip - 数字翻牌: {title, value(数字), prefix, suffix}
12. progress - 进度环: {title, percent(数字), color}
13. clock - 时钟: {format(24h/12h), showDate(布尔)}
14. marquee - 滚动字幕: {text, speed(默认50)}
15. border-box - 装饰边框: {title, style(tech-1/tech-2/simple), glowing(布尔)}
16. map - 中国地图: {title, borderStyle(tech-1/tech-2/simple/不填=无边框)}
    - 数据绑定: dataSource.mapping = { "name": "省份/城市字段", "value": "数值字段" }

【重要】所有图表组件(line/bar/pie/gauge/radar/scatter/ranking/table/map)都支持 borderStyle 属性：
- borderStyle: "tech-1" → 蓝色科幻发光边框
- borderStyle: "tech-2" → 紫色科幻发光边框
- borderStyle: "simple" → 简洁线框
- 不设置或 "none" → 无边框

画布尺寸: 1920 x 1080
布局原则：
- 第一行放标题(text组件，居中，大字号)
- 第二行放 KPI 指标卡（3-5个横排）
- 下面放图表（折线图+柱状图+饼图组合）
- 组件之间留 20px 间距
- KPI 卡片宽度 280-300，高度 140-160
- 图表宽度 400-600，高度 280-340

大屏/科技风格布局（当用户要求"大屏""科技""炫酷"时使用）：
- 必须包含一个 map 地图组件，放画布中央（x≈480, y≈115, 宽960, 高700），作为视觉核心
- 其他图表分列地图两侧，左列(x=40, 宽420)和右列(x=1460, 宽420)
- 为所有图表组件添加 borderStyle: "tech-1" 或 "tech-2"（蓝色或紫色发光边框）
- 标题建议用大字号(fontSize≥28)居中

增量模式：
- 已有组件不要覆盖，查看其 pos 和 size，新组件放空白区域
- 只用 ADD_WIDGET，不删除不修改已有组件，避免重复类型

数据源绑定规则：
- 如果用户有数据源，尽量为每个组件绑定数据源
- dataSource.sourceId 必须使用用户数据源列表中的 id
- mapping 中的字段名必须使用数据源的 fields 中存在的字段
- KPI 指标卡的 value 在 props 中写示例值（如"1,234"），同时在 dataSource.mapping 中指定真实字段
- 没有数据源时不要添加 dataSource 字段，用 props 中的假数据即可"""

SCENE_DATA_AWARE_ADDITION = """
用户已有以下数据源：
{data_sources}

请根据数据源的字段选择最合适的图表类型：
- 有时间字段 + 数值字段 → 折线图（mapping.x=时间字段, mapping.y=数值字段）
- 有分类字段 + 数值字段 → 柱状图或饼图
- 有省份/城市/地域名称 + 数值字段 → map 中国地图（mapping.name=地域字段, mapping.value=数值字段）
- 单一数值指标 → KPI 指标卡（mapping.value=字段名）
- 排名/top → 排行榜

每个图表的 title 要基于数据字段含义取名。
KPI 的 value 用合理的示例数值（如果有 sample 数据就用真实值）。
必须在每个图表组件中设置 dataSource.sourceId 和对应的 mapping。

【重要：SQL 推断】
如果数据源类型是 database，必须在 dataSource 中加 sql 字段：
- line/bar: sql 应包含 GROUP BY + SUM/COUNT + ORDER BY
- pie: sql 应包含 GROUP BY + SUM/COUNT + LIMIT 10
- kpi/number-flip: sql 应是 SELECT SUM/COUNT/AVG 返回单行
- ranking: sql 应包含 ORDER BY DESC + LIMIT 10
- table: sql 应包含 LIMIT 50
- 所有 SQL 必须加 LIMIT
- 不要 SELECT *，只选需要的字段

示例：
{{
  "dataSource": {{
    "sourceId": "ds_xxx",
    "mapping": {{"x": "month", "y": "total_sales"}},
    "sql": "SELECT month, SUM(amount) as total_sales FROM orders GROUP BY month ORDER BY month LIMIT 50"
  }}
}}"""


class SceneAgent(BaseAgent):
    name = "scene"
    description = "根据需求一次性生成完整看板"

    async def execute(self, message: str, context: dict) -> dict:
        system_prompt = SCENE_SYSTEM_PROMPT

        # 数据感知：如果有数据源，加入 prompt
        data_sources = context.get("dataSources", [])
        if data_sources:
            ds_text = ""
            for ds in data_sources:
                fields = ds.get("fields", [])
                sample = ds.get("sample", [])
                ds_text += f"- id={ds.get('id', '?')} name={ds.get('name', '未命名')}({ds.get('type')}): 字段 {fields}"
                if sample:
                    ds_text += f", 示例: {json.dumps(sample[:2], ensure_ascii=False)}"
                ds_text += "\n"
            system_prompt += SCENE_DATA_AWARE_ADDITION.format(data_sources=ds_text)

        context_summary = self.build_context_summary(context)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"用户需求：{message}\n\n当前状态：\n{context_summary}"},
        ]

        result = await chat_completion_json(messages)

        # 确保返回格式正确
        if "commands" not in result:
            result = {"commands": [], "message": "未能生成有效的看板布局"}

        if not isinstance(result.get("commands"), list):
            result["commands"] = []

        for cmd in result["commands"]:
            if isinstance(cmd, dict) and cmd.get("type") == "ADD_WIDGET":
                payload = cmd.get("payload") or {}
                payload.setdefault("position", {"x": 80, "y": 80})
                payload.setdefault("size", {"w": 300, "h": 200})
                payload.setdefault("props", {})
                cmd["payload"] = payload

        return result
