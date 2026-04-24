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

ADD_WIDGET 的 payload: {type, props, position:{x,y}, size:{w,h}}
UPDATE_WIDGET 的 payload: {id, props:{要更新的属性}}
DELETE_WIDGET 的 payload: {id}

可用组件类型: text, kpi, line, bar, pie
画布尺寸: 1920 x 1080

注意：
- 如果用户说"加一个XX"，用 ADD_WIDGET
- 如果用户说"改一下XX"或"把XX改成YY"，用 UPDATE_WIDGET，只传需要改的属性
- 如果用户说"删除XX"，用 DELETE_WIDGET
- 修改和删除时必须使用用户选中的组件 ID"""


class ComponentAgent(BaseAgent):
    name = "component"
    description = "处理单个组件的增删改"

    async def execute(self, message: str, context: dict) -> dict:
        context_summary = self.build_context_summary(context)

        messages = [
            {"role": "system", "content": COMPONENT_SYSTEM_PROMPT},
            {"role": "user", "content": f"用户指令：{message}\n\n当前状态：\n{context_summary}"},
        ]

        result = await chat_completion_json(messages, temperature=0.5)
        if "commands" not in result:
            result = {"commands": [], "message": "未能理解指令"}
        return result
