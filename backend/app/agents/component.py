"""
组件 Agent - 处理单个组件的创建、修改、删除
"""
from app.agents.base import BaseAgent
from app.services.kimi import chat_completion_json

COMPONENT_SYSTEM_PROMPT = """你是看板组件操作助手。根据用户的指令，生成对应的操作命令。

你必须返回一个 JSON 对象：
{
  "commands": [
    {
      "type": "ADD_WIDGET" 或 "UPDATE_WIDGET" 或 "DELETE_WIDGET",
      "payload": { ... }
    }
  ],
  "message": "描述你做了什么的中文说明"
}

ADD_WIDGET 的 payload: {type, props, position:{x,y}, size:{w,h}, dataSource:{sourceId, mapping}}
UPDATE_WIDGET 的 payload: {id, props:{要更新的属性}, dataSource:{sourceId, mapping}}
DELETE_WIDGET 的 payload: {id}

可用组件类型:
- text: 标题文本 {content, fontSize, align, color}
- kpi: KPI 指标卡 {title, value, unit, trend, color}
- line: 折线图 {title, smooth, area}
- bar: 柱状图 {title, stack, horizontal}
- pie: 饼图 {title, donut, showLabel}
- ranking: 排行榜 {title, showBar, maxItems}
- table: 数据表格 {title, sortable}
- gauge: 仪表盘 {title, value, min, max}
- radar: 雷达图 {title}
- scatter: 散点图 {title, xName, yName}
- number-flip: 数字翻牌 {title, value, prefix, suffix}
- progress: 进度环 {title, percent, color}
- clock: 时钟 {format, showDate}
- marquee: 滚动字幕 {text, speed}
- border-box: 装饰边框 {title, style, glowing}

画布尺寸: 1920 x 1080

数据源绑定 mapping 格式:
- line/bar: {x: "字段名", y: "字段名"}
- pie/ranking/table: {name: "字段名", value: "字段名"}
- kpi/number-flip: {value: "字段名"}
- gauge: {value: "字段名"}
- scatter: {x: "字段名", y: "字段名"}

规则：
- "加一个XX" → ADD_WIDGET
- "改一下XX"/"把XX改成YY" → UPDATE_WIDGET，只传需要改的属性
- "删除XX" → DELETE_WIDGET
- UPDATE/DELETE 必须使用选中组件 ID（如果没有选中组件，返回 message 提示用户先选中）
- ADD_WIDGET 放在画布空白区域，避开已有组件"""


class ComponentAgent(BaseAgent):
    name = "component"
    description = "处理单个组件的增删改"

    async def execute(self, message: str, context: dict) -> dict:
        context_summary = self.build_context_summary(context)

        messages = [
            {"role": "system", "content": COMPONENT_SYSTEM_PROMPT},
            {"role": "user", "content": f"用户指令：{message}\n\n当前状态：\n{context_summary}"},
        ]

        result = await chat_completion_json(messages)
        if "commands" not in result:
            result = {"commands": [], "message": "未能理解指令"}
        if not isinstance(result.get("commands"), list):
            result["commands"] = []
        return result
