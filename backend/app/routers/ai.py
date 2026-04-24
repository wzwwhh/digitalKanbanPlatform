"""
AI 路由 - 三层意图路由 + Agent 调度

Level 1: 正则匹配（0 token）
Level 2: 关键词匹配（0 token）
Level 3: Agent 调用（Kimi token）
"""
import re
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.agents.scene import SceneAgent
from app.agents.component import ComponentAgent

router = APIRouter()

# Agent 实例
scene_agent = SceneAgent()
component_agent = ComponentAgent()


class ChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    commands: list = []
    message: str = ""


# ========== Level 1: 正则规则（0 token）==========

REGEX_RULES = [
    # 删除
    (r"^删除(这个|当前|选中)?$", "DELETE_SELECTED"),
    # 复制
    (r"^复制(这个|当前|选中)?$", "DUPLICATE_SELECTED"),
    # 移动
    (r"^(左移|右移|上移|下移)(\d+)?$", "MOVE_DIRECTION"),
    # 放大缩小
    (r"^(放大|缩小)(\d+)?$", "RESIZE_DIRECTION"),
    # 标题修改
    (r"^(?:标题|名称)(?:改|换)(?:成|为)(.+)$", "RENAME_TITLE"),
]


def try_regex_match(message: str, context: dict) -> Optional[dict]:
    """Level 1: 正则匹配，0 token 开销"""
    msg = message.strip()
    selected_id = (context or {}).get("selectedId")

    for pattern, action in REGEX_RULES:
        match = re.match(pattern, msg)
        if not match:
            continue

        if action == "DELETE_SELECTED" and selected_id:
            return {
                "commands": [{"type": "DELETE_WIDGET", "payload": {"id": selected_id}}],
                "message": "已删除选中组件"
            }

        elif action == "MOVE_DIRECTION" and selected_id:
            direction = match.group(1)
            distance = int(match.group(2)) if match.group(2) else 50
            dx, dy = 0, 0
            if direction == "左移": dx = -distance
            elif direction == "右移": dx = distance
            elif direction == "上移": dy = -distance
            elif direction == "下移": dy = distance

            # 获取当前位置
            widgets = (context or {}).get("widgets", [])
            widget = next((w for w in widgets if w.get("id") == selected_id), None)
            if widget:
                pos = widget.get("position", {"x": 0, "y": 0})
                return {
                    "commands": [{"type": "MOVE_WIDGET", "payload": {
                        "id": selected_id,
                        "position": {"x": max(0, pos["x"] + dx), "y": max(0, pos["y"] + dy)}
                    }}],
                    "message": f"已{direction} {distance}px"
                }

        elif action == "RESIZE_DIRECTION" and selected_id:
            direction = match.group(1)
            amount = int(match.group(2)) if match.group(2) else 50
            widgets = (context or {}).get("widgets", [])
            widget = next((w for w in widgets if w.get("id") == selected_id), None)
            if widget:
                size = widget.get("size", {"w": 200, "h": 150})
                factor = 1 if direction == "放大" else -1
                return {
                    "commands": [{"type": "RESIZE_WIDGET", "payload": {
                        "id": selected_id,
                        "size": {
                            "w": max(80, size["w"] + amount * factor),
                            "h": max(60, size["h"] + amount * factor)
                        }
                    }}],
                    "message": f"已{direction}"
                }

        elif action == "RENAME_TITLE" and selected_id:
            new_title = match.group(1).strip()
            return {
                "commands": [{"type": "UPDATE_WIDGET", "payload": {
                    "id": selected_id,
                    "props": {"title": new_title}
                }}],
                "message": f"标题已改为「{new_title}」"
            }

    return None


# ========== Level 2: 关键词匹配（0 token）==========

THEME_KEYWORDS = {
    "暗色": "dark-tech", "深色": "dark-tech", "科技": "dark-tech",
    "亮色": "light-biz", "浅色": "light-biz", "商务": "light-biz",
    "霓虹": "cyber-neon", "赛博": "cyber-neon", "炫酷": "cyber-neon",
}


def try_keyword_match(message: str, context: dict) -> Optional[dict]:
    """Level 2: 关键词匹配，0 token 开销"""
    msg = message.strip()

    # 主题切换
    if any(k in msg for k in ["主题", "风格", "皮肤"]):
        for keyword, theme_id in THEME_KEYWORDS.items():
            if keyword in msg:
                return {
                    "commands": [{"type": "CHANGE_THEME", "payload": {"theme": theme_id}}],
                    "message": f"已切换到{keyword}主题"
                }

    # 撤销/重做
    if any(k in msg for k in ["撤销", "回退"]):
        return {"commands": [{"type": "UNDO"}], "message": "已撤销"}
    if any(k in msg for k in ["重做", "恢复"]):
        return {"commands": [{"type": "REDO"}], "message": "已重做"}

    return None


# ========== Level 3: Agent 路由（Kimi token）==========

def route_to_agent(message: str) -> str:
    """根据消息内容选择 Agent"""
    msg = message.strip()

    # 场景级别：生成完整看板
    if any(k in msg for k in ["看板", "驾驶舱", "大屏", "面板", "仪表板"]):
        return "scene"

    # 组件级别
    if any(k in msg for k in ["加一个", "添加", "新增", "创建"]):
        return "component"
    if any(k in msg for k in ["改成", "换成", "修改", "更新", "调整"]):
        return "component"

    # 默认用场景 Agent
    return "scene"


# ========== 主路由 ==========

@router.post("/chat", response_model=ChatResponse)
async def ai_chat(request: ChatRequest):
    """三层意图路由"""
    message = request.message.strip()
    context = request.context or {}

    # Level 1: 正则
    result = try_regex_match(message, context)
    if result:
        return ChatResponse(**result)

    # Level 2: 关键词
    result = try_keyword_match(message, context)
    if result:
        return ChatResponse(**result)

    # Level 3: Agent (调 Kimi)
    agent_name = route_to_agent(message)

    try:
        if agent_name == "scene":
            result = await scene_agent.execute(message, context)
        elif agent_name == "component":
            result = await component_agent.execute(message, context)
        else:
            result = await scene_agent.execute(message, context)

        return ChatResponse(**result)
    except Exception as e:
        return ChatResponse(
            commands=[],
            message=f"AI 处理出错: {str(e)}"
        )
