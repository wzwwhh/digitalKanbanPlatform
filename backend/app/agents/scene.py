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
        "size": { "w": 数字, "h": 数字 }
      }
    }
  ],
  "message": "描述你做了什么的中文说明"
}

可用组件类型和属性：
1. text - 标题文本: {content, fontSize(默认24), align(left/center/right), color}
2. kpi - KPI指标卡: {title, value, unit, trend(up/down/flat), color}
3. line - 折线图: {title, smooth(布尔), area(布尔)}
4. bar - 柱状图: {title, stack(布尔), horizontal(布尔)}
5. pie - 饼图: {title, donut(布尔), showLabel(布尔)}

画布尺寸: 1920 x 1080
布局原则：
- 第一行放标题(text组件，居中，大字号)
- 第二行放 KPI 指标卡（3-5个横排）
- 下面放图表（折线图+柱状图+饼图组合）
- 组件之间留 20px 间距
- KPI 卡片宽度 280-300，高度 140-160
- 图表宽度 400-600，高度 280-340"""

SCENE_DATA_AWARE_ADDITION = """
用户已有以下数据源：
{data_sources}

请根据数据源的字段选择最合适的图表类型：
- 有时间字段 + 数值字段 → 折线图
- 有分类字段 + 数值字段 → 柱状图或饼图
- 单一数值指标 → KPI 指标卡
- 排名/top → 排行榜

每个图表的 title 要基于数据字段含义取名。
KPI 的 value 用合理的示例数值（如果有 sample 数据就用真实值）。"""


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
                ds_text += f"- {ds.get('name', '未命名')}({ds.get('type')}): 字段 {fields}"
                if sample:
                    ds_text += f", 示例: {json.dumps(sample[:2], ensure_ascii=False)}"
                ds_text += "\n"
            system_prompt += SCENE_DATA_AWARE_ADDITION.format(data_sources=ds_text)

        context_summary = self.build_context_summary(context)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"用户需求：{message}\n\n当前状态：\n{context_summary}"},
        ]

        result = await chat_completion_json(messages, temperature=0.7)

        # 确保返回格式正确
        if "commands" not in result:
            result = {"commands": [], "message": "未能生成有效的看板布局"}

        return result
