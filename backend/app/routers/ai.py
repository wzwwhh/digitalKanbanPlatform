"""
AI 路由 - 三层意图路由 + Agent 调度

Level 1: 正则匹配（0 token）
Level 2: 关键词匹配（0 token）
Level 3: Agent 调用（Kimi token）

所有 AI 常量配置集中在 app/ai_config.py
"""
import re
import json
import asyncio
import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from app.agents.scene import SceneAgent
from app.agents.component import ComponentAgent
from app.agents.layout import LayoutAgent
from app.services.kimi import chat_completion_json
from app.ai_config import (
    REGEX_RULES, THEME_KEYWORDS, COLOR_MAP, CHART_TYPE_MAP,
    THEME_TRIGGERS, COLOR_TRIGGERS, CHART_TRIGGERS,
    SCENE_KEYWORDS, SCENE_INCREMENT_KEYWORDS,
    LAYOUT_KEYWORDS,
    COMPONENT_ADD_KEYWORDS, COMPONENT_EDIT_KEYWORDS,
    COMPONENT_DATA_KEYWORDS, COMPONENT_UNBIND_KEYWORDS,
    CHART_SUGGESTIONS,
    MAX_MOVE_DISTANCE, MAX_RESIZE_AMOUNT,
    MAX_WIDGET_WIDTH, MAX_WIDGET_HEIGHT,
    MIN_WIDGET_WIDTH, MIN_WIDGET_HEIGHT,
    ANALYSIS_KEYWORDS, BACKGROUND_TRIGGERS,
    INTENT_CLASSIFY_PROMPT,
)

router = APIRouter()

# Agent 实例
scene_agent = SceneAgent()
component_agent = ComponentAgent()
layout_agent = LayoutAgent()


class ChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    commands: list = []
    message: str = ""


# ========== Level 1: 正则（规则定义在 ai_config.py）==========


def try_regex_match(message: str, context: dict) -> Optional[dict]:
    """Level 1: 正则匹配，0 token 开销"""
    msg = message.strip()
    selected_id = (context or {}).get("selectedId")

    for pattern, action in REGEX_RULES:
        match = re.match(pattern, msg)
        if not match:
            continue

        # 需要选中组件但未选中 → 友好提示
        if action in ("DELETE_SELECTED", "DUPLICATE_SELECTED", "MOVE_DIRECTION",
                      "RESIZE_DIRECTION", "RENAME_TITLE") and not selected_id:
            return {
                "commands": [],
                "message": "请先在画布上点击选中一个组件，再执行此操作"
            }

        if action == "DELETE_SELECTED":
            return {
                "commands": [{"type": "DELETE_WIDGET", "payload": {"id": selected_id}}],
                "message": "已删除选中组件"
            }

        elif action == "DUPLICATE_SELECTED":
            widgets = (context or {}).get("widgets", [])
            widget = next((w for w in widgets if w.get("id") == selected_id), None)
            if widget:
                pos = widget.get("position", {"x": 0, "y": 0})
                return {
                    "commands": [{"type": "ADD_WIDGET", "payload": {
                        "type": widget.get("type", "kpi"),
                        "props": widget.get("props", {}),
                        "position": {"x": pos.get("x", 0) + 30, "y": pos.get("y", 0) + 30},
                        "size": widget.get("size", {"w": 200, "h": 150}),
                        "dataSource": widget.get("dataSource"),
                    }}],
                    "message": "已复制组件"
                }

        elif action == "MOVE_DIRECTION":
            direction = match.group(1)
            distance = int(match.group(2)) if match.group(2) else 50
            distance = max(1, min(distance, MAX_MOVE_DISTANCE))  # 限制范围
            dx, dy = 0, 0
            if direction == "左移": dx = -distance
            elif direction == "右移": dx = distance
            elif direction == "上移": dy = -distance
            elif direction == "下移": dy = distance

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

        elif action == "RESIZE_DIRECTION":
            direction = match.group(1)
            amount = int(match.group(2)) if match.group(2) else 50
            amount = max(1, min(amount, MAX_RESIZE_AMOUNT))  # 限制范围
            widgets = (context or {}).get("widgets", [])
            widget = next((w for w in widgets if w.get("id") == selected_id), None)
            if widget:
                size = widget.get("size", {"w": 200, "h": 150})
                factor = 1 if direction == "放大" else -1
                new_w = max(MIN_WIDGET_WIDTH, min(MAX_WIDGET_WIDTH, size["w"] + amount * factor))
                new_h = max(MIN_WIDGET_HEIGHT, min(MAX_WIDGET_HEIGHT, size["h"] + amount * factor))
                return {
                    "commands": [{"type": "RESIZE_WIDGET", "payload": {
                        "id": selected_id,
                        "size": {"w": new_w, "h": new_h}
                    }}],
                    "message": f"已{direction}"
                }

        elif action == "RENAME_TITLE":
            new_title = match.group(1).strip()
            return {
                "commands": [{"type": "UPDATE_WIDGET", "payload": {
                    "id": selected_id,
                    "props": {"title": new_title}
                }}],
                "message": f"标题已改为「{new_title}」"
            }

    return None


# ========== Level 2: 关键词匹配（常量定义在 ai_config.py）==========


async def try_keyword_match(message: str, context: dict) -> Optional[dict]:
    """
    Level 2: 关键词匹配，0 token 开销。
    
    设计原则：
    - 双重验证：触发词 + 操作目标 都要匹配才执行
    - 宁可漏过，不可误触（漏过的交给 Level 3 LLM 处理）
    - 单字颜色("绿""白") 在与主题关键词重叠时不参与匹配
    """
    msg = message.strip()
    widgets = (context or {}).get("widgets", [])
    selected_id = (context or {}).get("selectedId")

    # === 主题切换 ===
    # 要求：消息包含主题触发词 + 具体主题关键词
    if any(t in msg for t in THEME_TRIGGERS):
        for keyword, theme_id in THEME_KEYWORDS.items():
            if keyword in msg:
                return {
                    "commands": [{"type": "CHANGE_THEME", "payload": {"theme": theme_id}}],
                    "message": f"已切换到「{keyword}」主题"
                }
        # 有触发词但无具体主题 → 不匹配，让 LLM 处理

    # === 撤销/重做 ===
    # 精确匹配：只在短消息且不含其他动词时触发
    if len(msg) <= 6:
        if any(msg.startswith(k) for k in ["撤销", "回退", "撤回"]):
            return {"commands": [{"type": "UNDO"}], "message": "已撤销上一步操作"}
        if any(msg.startswith(k) for k in ["重做", "恢复操作"]):
            return {"commands": [{"type": "REDO"}], "message": "已重做"}

    # === 批量颜色修改 ===
    # 双重验证：包含颜色触发词 + 有效颜色名
    if any(t in msg for t in COLOR_TRIGGERS):
        target_color = None
        matched_name = ""
        # 优先匹配长关键词（"红色"优先于"红"）
        for color_name in sorted(COLOR_MAP.keys(), key=len, reverse=True):
            if color_name in msg:
                target_color = COLOR_MAP[color_name]
                matched_name = color_name
                break
        if target_color and widgets:
            is_batch = any(k in msg for k in ["所有", "全部", "每个", "批量"])
            if is_batch:
                cmds = [{
                    "type": "UPDATE_WIDGET",
                    "payload": {"id": w.get("id"), "props": {"color": target_color}}
                } for w in widgets]
                return {
                    "commands": [{"type": "BATCH", "payload": {"commands": cmds}}],
                    "message": f"已将全部 {len(cmds)} 个组件颜色改为{matched_name} ({target_color})"
                }
            elif selected_id:
                return {
                    "commands": [{"type": "UPDATE_WIDGET", "payload": {
                        "id": selected_id, "props": {"color": target_color}
                    }}],
                    "message": f"已将选中组件颜色改为{matched_name}"
                }

    # === 图表类型切换 ===
    # 三重验证：有选中组件 + 包含切换触发词 + 具体图表类型名
    if selected_id and any(t in msg for t in CHART_TRIGGERS):
        for chart_name, chart_type in CHART_TYPE_MAP.items():
            if chart_name in msg:
                sel_widget = next((w for w in widgets if w.get("id") == selected_id), None)
                if sel_widget and sel_widget.get("type") in ("line", "bar", "pie"):
                    return {
                        "commands": [{
                            "type": "UPDATE_WIDGET",
                            "payload": {
                                "id": selected_id,
                                "type": chart_type,
                                "props": {**sel_widget.get("props", {})}
                            }
                        }],
                        "message": f"已将图表切换为{chart_name}"
                    }

    # === 背景色 / 底色修改 ===
    if any(t in msg for t in BACKGROUND_TRIGGERS):
        # 先尝试匹配主题
        for keyword, theme_id in THEME_KEYWORDS.items():
            if keyword in msg:
                return {
                    "commands": [{"type": "CHANGE_THEME", "payload": {"theme": theme_id}}],
                    "message": f"已将背景切换为「{keyword}」主题"
                }
        # 尝试匹配颜色 → 推荐最接近的主题
        for color_name in sorted(COLOR_MAP.keys(), key=len, reverse=True):
            if color_name in msg:
                # 深色系推荐暗色主题，浅色系推荐亮色主题
                if color_name in ("白色", "白"):
                    theme = "minimal-white"
                elif color_name in ("绿色", "绿"):
                    theme = "forest-green"
                elif color_name in ("紫色", "紫", "粉色", "粉"):
                    theme = "cyber-neon"
                else:
                    theme = "dark-tech"
                return {
                    "commands": [{"type": "CHANGE_THEME", "payload": {"theme": theme}}],
                    "message": f"已将背景切换为最接近「{color_name}」的主题"
                }
        # 没匹配到具体颜色，给提示
        return {
            "commands": [],
            "message": '支持的背景主题：暗色/科技蓝、亮色/商务、霓虹/赛博、极简白、森林绿。请说"换XX主题"来切换。'
        }

    # === 排版 ===
    if any(k in msg for k in LAYOUT_KEYWORDS) and widgets:
        # 从 context 读取模式（前端可传 layout_mode: 'ai' 或 'fast'）
        layout_mode = (context or {}).get("layout_mode", "ai")
        layout_result = await do_layout(message, context, widgets, layout_mode)
        if layout_result:
            return layout_result

    # 未匹配 → 交给 Level 3 (LLM Agent) 处理
    return None


async def do_layout(message: str, context: dict, widgets: list, mode: str = "ai") -> Optional[dict]:
    """
    排版调度：
    - mode='fast': 直接用本地算法（快速、稳定）
    - mode='ai': 先尝试 AI，失败回退本地算法
    """
    if mode == "fast":
        print(f"[排版] 快速排版模式，{len(widgets)} 个组件")
        return compute_layout(widgets)

    # AI 模式：先尝试 AI，失败回退本地
    try:
        print(f"[排版] AI 排版模式，{len(widgets)} 个组件")
        result = await layout_agent.execute(message, context)
        if result and result.get("commands") and len(result["commands"]) > 0:
            print(f"[排版] AI 排版成功")
            result["message"] = "✨ " + (result.get("message") or "AI 排版完成")
            return result
        else:
            print("[排版] AI 排版返回空命令，回退到本地算法")
    except Exception as e:
        print(f"[排版] AI 排版失败: {e}，回退到本地算法")

    print("[排版] 使用本地算法兜底")
    return compute_layout(widgets)


def compute_layout(widgets: list) -> Optional[dict]:
    """
    确定性排版算法 — 自适应 1920×1080 画布

    双模式：
    - 有 map 组件 → 中央卫星大屏布局（地图居中，其他组件分列两侧）
    - 无 map 组件 → 传统流水线布局（从上到下分行排列）
    """
    # 先分类，看有没有 map
    maps = []
    others = []
    for w in widgets:
        t = w.get("type", "")
        wid = w.get("id")
        if not wid:
            continue
        if t == "map":
            maps.append(w)
        else:
            others.append(w)

    if maps:
        print(f"[排版] 检测到 {len(maps)} 个地图组件，使用中央卫星布局")
        return _compute_bigscreen_layout(widgets, maps)
    else:
        print(f"[排版] 无地图组件，使用传统流水线布局")
        return _compute_flow_layout(widgets)


def _compute_bigscreen_layout(widgets: list, maps: list) -> Optional[dict]:
    """
    中央卫星大屏布局 — 地图居中，其他组件分列两侧

    ┌──────────────────────────────────────────────┐
    │                   标  题                      │
    ├────────────┬──────────────────┬───────────────┤
    │  左列组件  │                  │  右列组件      │
    │  (指标+图) │    中 国 地 图    │  (指标+图)     │
    │            │  （视觉核心 C位） │               │
    ├────────────┴──────────────────┴───────────────┤
    │                 滚动字幕                       │
    └──────────────────────────────────────────────┘
    """
    CANVAS_W = 1920
    CANVAS_H = 1080
    MARGIN = 40
    GAP = 20
    TITLE_H = 55
    MARQUEE_H = 45

    SIDE_W = 420        # 左右两列宽度
    MAP_W = CANVAS_W - MARGIN * 2 - SIDE_W * 2 - GAP * 2  # ≈ 960

    # ===== 分类 =====
    titles = []
    indicators = []
    charts = []
    data_widgets = []
    clocks = []
    marquees = []

    for w in widgets:
        t = w.get("type", "")
        wid = w.get("id")
        if not wid or t == "map":
            continue
        if t == "text":
            titles.append(w)
        elif t in ("kpi", "number-flip", "progress"):
            indicators.append(w)
        elif t in ("line", "bar", "pie", "gauge", "radar", "scatter"):
            charts.append(w)
        elif t in ("table", "ranking"):
            data_widgets.append(w)
        elif t == "clock":
            clocks.append(w)
        elif t == "marquee":
            marquees.append(w)

    commands = []
    current_y = MARGIN

    # --- 标题：顶部全宽 ---
    if titles:
        for tw in titles:
            commands.append({"type": "MOVE_WIDGET", "payload": {"id": tw["id"], "position": {"x": MARGIN, "y": current_y}}})
            commands.append({"type": "RESIZE_WIDGET", "payload": {"id": tw["id"], "size": {"w": CANVAS_W - MARGIN * 2, "h": TITLE_H}}})
        current_y += TITLE_H + GAP

    # --- 时钟：右上角（不占行）---
    if clocks:
        for cw in clocks:
            commands.append({"type": "MOVE_WIDGET", "payload": {"id": cw["id"], "position": {"x": CANVAS_W - MARGIN - 200, "y": MARGIN}}})
            commands.append({"type": "RESIZE_WIDGET", "payload": {"id": cw["id"], "size": {"w": 200, "h": 75}}})

    # --- 计算中间区域的可用高度 ---
    bottom_reserved = (MARQUEE_H + GAP) if marquees else 0
    body_h = CANVAS_H - current_y - MARGIN - bottom_reserved  # 中间区域总高

    # --- 地图：居中 ---
    map_x = MARGIN + SIDE_W + GAP
    map_y = current_y
    map_h = body_h
    for mw in maps:
        commands.append({"type": "MOVE_WIDGET", "payload": {"id": mw["id"], "position": {"x": map_x, "y": map_y}}})
        commands.append({"type": "RESIZE_WIDGET", "payload": {"id": mw["id"], "size": {"w": MAP_W, "h": map_h}}})

    # --- 分配侧边组件：指标卡 + 图表 + 数据组件交替放两侧 ---
    side_items = indicators + charts + data_widgets
    left_items = []
    right_items = []
    for i, item in enumerate(side_items):
        if i % 2 == 0:
            left_items.append(item)
        else:
            right_items.append(item)

    # 左列
    _layout_side_column(commands, left_items, x=MARGIN, y=current_y,
                        col_w=SIDE_W, total_h=body_h, gap=GAP)
    # 右列
    right_x = MARGIN + SIDE_W + GAP + MAP_W + GAP
    _layout_side_column(commands, right_items, x=right_x, y=current_y,
                        col_w=SIDE_W, total_h=body_h, gap=GAP)

    # --- 滚动字幕：底部全宽 ---
    if marquees:
        marquee_y = CANVAS_H - MARGIN - MARQUEE_H
        for mw in marquees:
            commands.append({"type": "MOVE_WIDGET", "payload": {"id": mw["id"], "position": {"x": MARGIN, "y": marquee_y}}})
            commands.append({"type": "RESIZE_WIDGET", "payload": {"id": mw["id"], "size": {"w": CANVAS_W - MARGIN * 2, "h": MARQUEE_H}}})

    if not commands:
        return None

    types_summary = {}
    for w in widgets:
        t = w.get("type", "unknown")
        types_summary[t] = types_summary.get(t, 0) + 1
    summary_parts = [f"{v}个{k}" for k, v in types_summary.items()]

    return {
        "commands": [{"type": "BATCH", "payload": {"commands": commands}}],
        "message": f"🗺️ 大屏排版完成！{len(widgets)} 个组件（{'、'.join(summary_parts)}），"
                   f"地图居中作为视觉核心，其他组件分列两侧。"
    }


def _layout_side_column(commands: list, items: list, x: int, y: int,
                         col_w: int, total_h: int, gap: int):
    """将一组组件在垂直列内均匀排列"""
    if not items:
        return
    n = len(items)
    item_h = max(120, (total_h - gap * (n - 1)) // n)
    current_y = y
    for item in items:
        commands.append({"type": "MOVE_WIDGET", "payload": {"id": item["id"], "position": {"x": x, "y": current_y}}})
        commands.append({"type": "RESIZE_WIDGET", "payload": {"id": item["id"], "size": {"w": col_w, "h": item_h}}})
        current_y += item_h + gap


def _compute_flow_layout(widgets: list) -> Optional[dict]:
    """
    传统流水线排版算法 — 自适应 1920×1080 画布（无地图时使用）

    按「标题 → 指标 → 图表 → 数据」从上到下分行排列。
    """
    CANVAS_W = 1920
    CANVAS_H = 1080
    MARGIN_X = 40
    MARGIN_Y = 20
    GAP_X = 20
    GAP_Y = 16
    USABLE_W = CANVAS_W - MARGIN_X * 2  # 1840

    # ===== 分类 =====
    titles = []
    indicators = []
    charts = []
    data_widgets = []
    clocks = []
    marquees = []

    for w in widgets:
        t = w.get("type", "")
        wid = w.get("id")
        if not wid:
            continue
        if t == "text":
            titles.append(w)
        elif t in ("kpi", "number-flip", "progress"):
            indicators.append(w)
        elif t in ("line", "bar", "pie", "gauge", "radar", "scatter"):
            charts.append(w)
        elif t in ("table", "ranking"):
            data_widgets.append(w)
        elif t == "clock":
            clocks.append(w)
        elif t == "marquee":
            marquees.append(w)

    # ===== 计算需要的行数和理想高度 =====
    TITLE_H = 55
    INDICATOR_H = 140
    MARQUEE_H = 45

    chart_rows_count = (len(charts) + 2) // 3 if charts else 0
    data_rows_count = (len(data_widgets) + 2) // 3 if data_widgets else 0

    fixed_h = MARGIN_Y * 2
    if titles:
        fixed_h += TITLE_H + GAP_Y
    if indicators:
        fixed_h += INDICATOR_H + GAP_Y
    if marquees:
        fixed_h += MARQUEE_H + GAP_Y

    flex_rows = chart_rows_count + data_rows_count
    if flex_rows == 0:
        flex_row_h = 300
    else:
        available_h = CANVAS_H - fixed_h - GAP_Y * max(0, flex_rows - 1)
        flex_row_h = max(200, min(380, available_h // flex_rows))

    # ===== 生成命令 =====
    commands = []
    current_y = MARGIN_Y

    # --- 标题 ---
    if titles:
        for tw in titles:
            commands.append({"type": "MOVE_WIDGET", "payload": {"id": tw["id"], "position": {"x": MARGIN_X, "y": current_y}}})
            commands.append({"type": "RESIZE_WIDGET", "payload": {"id": tw["id"], "size": {"w": USABLE_W, "h": TITLE_H}}})
        current_y += TITLE_H + GAP_Y

    # --- 时钟放右上角（不占行） ---
    if clocks:
        for cw in clocks:
            commands.append({"type": "MOVE_WIDGET", "payload": {"id": cw["id"], "position": {"x": CANVAS_W - MARGIN_X - 200, "y": MARGIN_Y}}})
            commands.append({"type": "RESIZE_WIDGET", "payload": {"id": cw["id"], "size": {"w": 200, "h": 75}}})

    # --- 指标卡（横向均匀居中）---
    if indicators:
        n = len(indicators)
        card_w = min(320, (USABLE_W - GAP_X * (n - 1)) // n)
        total_w = card_w * n + GAP_X * (n - 1)
        start_x = MARGIN_X + (USABLE_W - total_w) // 2
        for i, iw in enumerate(indicators):
            x = start_x + i * (card_w + GAP_X)
            commands.append({"type": "MOVE_WIDGET", "payload": {"id": iw["id"], "position": {"x": x, "y": current_y}}})
            commands.append({"type": "RESIZE_WIDGET", "payload": {"id": iw["id"], "size": {"w": card_w, "h": INDICATOR_H}}})
        current_y += INDICATOR_H + GAP_Y

    # --- 图表（每行最多3个，自适应高度）---
    if charts:
        rows = [charts[i:i+3] for i in range(0, len(charts), 3)]
        for row in rows:
            rn = len(row)
            chart_w = (USABLE_W - GAP_X * (rn - 1)) // rn
            for i, cw in enumerate(row):
                x = MARGIN_X + i * (chart_w + GAP_X)
                commands.append({"type": "MOVE_WIDGET", "payload": {"id": cw["id"], "position": {"x": x, "y": current_y}}})
                commands.append({"type": "RESIZE_WIDGET", "payload": {"id": cw["id"], "size": {"w": chart_w, "h": flex_row_h}}})
            current_y += flex_row_h + GAP_Y

    # --- 数据组件（表格/排行榜）---
    if data_widgets:
        rows = [data_widgets[i:i+3] for i in range(0, len(data_widgets), 3)]
        for row in rows:
            rn = len(row)
            data_w = (USABLE_W - GAP_X * (rn - 1)) // rn
            for i, dw in enumerate(row):
                x = MARGIN_X + i * (data_w + GAP_X)
                commands.append({"type": "MOVE_WIDGET", "payload": {"id": dw["id"], "position": {"x": x, "y": current_y}}})
                commands.append({"type": "RESIZE_WIDGET", "payload": {"id": dw["id"], "size": {"w": data_w, "h": flex_row_h}}})
            current_y += flex_row_h + GAP_Y

    # --- 滚动字幕放底部 ---
    if marquees:
        marquee_y = CANVAS_H - MARGIN_Y - MARQUEE_H
        for mw in marquees:
            commands.append({"type": "MOVE_WIDGET", "payload": {"id": mw["id"], "position": {"x": MARGIN_X, "y": marquee_y}}})
            commands.append({"type": "RESIZE_WIDGET", "payload": {"id": mw["id"], "size": {"w": USABLE_W, "h": MARQUEE_H}}})

    if not commands:
        return None

    types_summary = {}
    for w in widgets:
        t = w.get("type", "unknown")
        types_summary[t] = types_summary.get(t, 0) + 1
    summary_parts = [f"{v}个{k}" for k, v in types_summary.items()]

    return {
        "commands": [{"type": "BATCH", "payload": {"commands": commands}}],
        "message": f"已完成排版！共整理 {len(widgets)} 个组件（{'、'.join(summary_parts)}），"
                   f"按「标题 → 指标 → 图表 → 数据」分层排列。"
    }


# ========== Level 3: LLM 意图分类（约 30 token）==========

async def classify_intent(message: str) -> str:
    """用 LLM 做轻量意图分类，取代纯关键词路由"""
    msg = message.strip()

    # 快速预判：如果关键词明确，直接返回（省 token）
    if any(k in msg for k in ANALYSIS_KEYWORDS):
        return "analysis"
    if any(k in msg for k in SCENE_KEYWORDS + SCENE_INCREMENT_KEYWORDS):
        return "scene"
    if any(k in msg for k in COMPONENT_ADD_KEYWORDS):
        return "component"
    if any(k in msg for k in LAYOUT_KEYWORDS):
        return "layout"

    # 关键词不明确 → 调 LLM 分类（约 30 token）
    try:
        prompt = INTENT_CLASSIFY_PROMPT.format(message=msg)
        result = await chat_completion_json([
            {"role": "user", "content": prompt}
        ])
        intent = result.get("intent", "chat")
        if intent in ("scene", "component", "layout", "analysis", "chat"):
            print(f"[意图分类] LLM 判定: '{msg}' → {intent}")
            return intent
    except Exception as e:
        print(f"[意图分类] LLM 分类失败: {e}，走关键词兜底")

    # LLM 也失败 → 关键词兜底
    if any(k in msg for k in COMPONENT_EDIT_KEYWORDS + COMPONENT_DATA_KEYWORDS):
        return "component"

    # 最终兜底：对话（不操作画布）
    return "chat"


async def do_analysis(message: str, context: dict) -> dict:
    """分析/对话路径 — 不操作画布，纯文本回答"""
    from app.services.kimi import chat_completion

    # 构建上下文摘要
    widgets = (context or {}).get("widgets", [])
    selected_id = (context or {}).get("selectedId")
    data_sources = (context or {}).get("dataSources", [])

    context_parts = []
    if widgets:
        context_parts.append(f"画布上有 {len(widgets)} 个组件")
        # 如果有选中组件，详细描述
        if selected_id:
            sel = next((w for w in widgets if w.get("id") == selected_id), None)
            if sel:
                title = sel.get("title") or (sel.get("props") or {}).get("title", "")
                wtype = sel.get("type", "?")
                ds = sel.get("dataSource") or {}
                context_parts.append(f"选中组件: {wtype}「{title}」")
                if ds.get("sourceId"):
                    context_parts.append(f"绑定数据源: {ds.get('sourceId')}")
                    mapping = ds.get("mapping", {})
                    if mapping:
                        context_parts.append(f"字段映射: {mapping}")

    if data_sources:
        for ds in data_sources[:3]:
            fields = ds.get("fields", [])
            context_parts.append(f"数据源「{ds.get('name', '?')}」: {','.join(fields[:8])}")

    context_str = "\n".join(context_parts) if context_parts else "画布为空"

    system = """你是数据看板的 AI 助手。用户在问问题或请求分析。
请直接用中文回答，给出有价值的分析和建议。
不要返回 JSON，不要返回命令，只用自然语言回答。
如果涉及数据分析，基于上下文中的组件和数据源信息给出洞察。"""

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"用户问：{message}\n\n当前看板状态：\n{context_str}"},
    ]

    try:
        answer = await chat_completion(messages, response_format="text")
        return {"commands": [], "message": answer}
    except Exception as e:
        return {"commands": [], "message": f"分析失败: {str(e)}"}


# ========== 主路由 ==========

@router.post("/chat", response_model=ChatResponse)
async def ai_chat(request: ChatRequest):
    """四层意图路由"""
    message = request.message.strip()
    context = request.context or {}

    # Level 1: 正则（0 token）
    result = try_regex_match(message, context)
    if result:
        return ChatResponse(**result)

    # Level 2: 关键词（0 token）
    result = await try_keyword_match(message, context)
    if result:
        return ChatResponse(**result)

    # Level 3: LLM 意图分类 + Agent 调度
    intent = await classify_intent(message)
    print(f"[AI路由] 意图={intent}, 消息='{message}'")

    try:
        if intent == "analysis" or intent == "chat":
            # 分析/对话 — 不操作画布
            result = await do_analysis(message, context)
        elif intent == "scene":
            result = await scene_agent.execute(message, context)
        elif intent == "component":
            result = await component_agent.execute(message, context)
        elif intent == "layout":
            widgets = (context or {}).get("widgets", [])
            if widgets:
                layout_mode = context.get("layout_mode", "ai")
                result = await do_layout(message, context, widgets, layout_mode)
            else:
                result = {"commands": [], "message": "画布上没有组件，无法排版"}
        else:
            result = await do_analysis(message, context)

        return ChatResponse(**result)
    except Exception as e:
        return ChatResponse(
            commands=[],
            message=f"AI 处理出错: {str(e)}"
        )


# ========== SQL 推断端点（供前端绑定数据源 / AI 生成看板时调用）==========


class InferSqlRequest(BaseModel):
    widgetType: str
    dataSource: dict
    userIntent: Optional[str] = ""


@router.post("/infer-sql")
async def api_infer_sql(req: InferSqlRequest):
    """
    AI 推断组件最佳查询 SQL + 字段映射。
    
    调用场景：
    - 前端 PropEditor 绑定数据源后自动推断
    - AI 生成看板时为每个图表推断
    - 智能问数一键入板时
    """
    result = await infer_widget_sql(req.widgetType, req.dataSource, req.userIntent)
    return {"success": True, **result}


# ========== 智能问数（SSE 流式） ==========


class AskRequest(BaseModel):
    question: str
    allDataSources: Optional[list] = None
    projectId: Optional[str] = None


def sse_event(event_type: str, data: dict) -> str:
    """构建 SSE 事件字符串"""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def build_ds_metadata(all_ds: list) -> str:
    """构建紧凑的数据源元信息（仅字段名/类型/注释/样本，不含数据）"""
    parts = []
    for ds in all_ds:
        fields_info = []
        annotations = ds.get("fieldAnnotations") or {}
        for f in (ds.get("fields") or [])[:20]:
            ann = annotations.get(f, "")
            fields_info.append(f"{f}({ann})" if ann else f)

        info = f"[{ds.get('id')}] {ds.get('name','未命名')}"
        ds_type = ds.get("type", "api")
        info += f"  类型: {ds_type}"
        if ds_type == "database":
            info += f" | 表: {ds.get('table','?')}"
        info += f"\n  字段: {', '.join(fields_info)}"
        sample = ds.get("sample", [])[:2]
        if sample:
            info += f"\n  样本: {json.dumps(sample, ensure_ascii=False)[:300]}"
        parts.append(info)
    return "\n\n".join(parts)


async def infer_widget_sql(widget_type: str, ds: dict, user_intent: str = "") -> dict:
    """
    通用 SQL 推断能力 —— 任何 AI 场景只要涉及"组件 + 数据源"都调用此函数。
    
    根据组件类型、数据源字段/注释/样本，AI 自动推断出：
    - sql: 合适的查询语句（聚合/筛选/排序）
    - mapping: 字段映射（x/y/name/value 等）
    
    使用场景：
    1. SceneAgent 生成看板时：为每个图表推断 SQL
    2. ComponentAgent 添加组件时：为新组件推断 SQL
    3. 智能问数一键入板时：widgetConfig 携带推断的 SQL
    4. PropEditor 手动绑定数据源时：自动推荐 SQL
    """
    annotations = ds.get("fieldAnnotations") or {}
    fields_desc = []
    for f in (ds.get("fields") or [])[:20]:
        ann = annotations.get(f, "")
        fields_desc.append(f"{f}({ann})" if ann else f)
    
    sample = ds.get("sample", [])[:3]
    ds_type = ds.get("type", "api")
    table = ds.get("table", "")
    
    prompt = f"""根据组件类型和数据源信息，推断最佳的查询方式。

组件类型: {widget_type}
用户意图: {user_intent or '（未指定，请根据组件类型和数据特征自动判断）'}

数据源: {ds.get('name', '未命名')} (类型: {ds_type})
{"表: " + table if table else ""}
字段: {', '.join(fields_desc)}
样本: {json.dumps(sample, ensure_ascii=False)[:400] if sample else '无'}

请返回 JSON:
{{
  "sql": "SELECT语句（仅database类型需要，api类型留空）",
  "mapping": {{"字段映射"}},
  "title": "建议的组件标题（中文）"
}}

SQL 推断逻辑：
- line(折线图): 需要时间/类别字段做X轴，数值字段做Y轴，通常需 GROUP BY + SUM/AVG + ORDER BY
- bar(柱状图): 类似折线图，按分类聚合
- pie(饼图): 需要 GROUP BY 分类 + SUM/COUNT，通常 LIMIT 10
- kpi(指标卡): SELECT SUM/COUNT/AVG 单一聚合值
- number-flip(翻牌器): 同 kpi
- gauge(仪表盘): SELECT 单一百分比/比率值
- ranking(排行榜): SELECT 名称,数值 ORDER BY 数值 DESC LIMIT 10
- table(数据表): SELECT 所需字段 LIMIT 50
- scatter(散点): 两个数值字段

mapping 格式：
- line/bar: {{"x": "X轴字段名", "y": "Y轴字段名"}}
- pie/ranking: {{"name": "名称字段", "value": "数值字段"}}
- kpi/number-flip/gauge: {{"value": "数值字段"}}
- table: {{"name": "名称字段", "value": "数值字段"}}
- scatter: {{"x": "X字段", "y": "Y字段"}}

规则：
- SQL 只允许 SELECT，必须加 LIMIT（最大 200）
- SQL 应精准，不要 SELECT *（除非 table 组件）
- api 类型的 sql 填空字符串
- title 要有业务含义（如"月度销售趋势"而非"折线图"）"""

    try:
        result = await chat_completion_json([
            {"role": "system", "content": "你是SQL推断专家，只返回紧凑JSON。"},
            {"role": "user", "content": prompt}
        ])
        # 确保返回格式
        return {
            "sql": result.get("sql", ""),
            "mapping": result.get("mapping", {}),
            "title": result.get("title", ""),
        }
    except Exception as e:
        print(f"[SQL推断] 失败: {e}")
        return {"sql": "", "mapping": {}, "title": ""}


async def generate_query_plan(question: str, ds_metadata: str) -> dict:
    """
    Phase 1: AI 生成查询方案（JSON 模式，紧凑 prompt）
    
    输入：问题 + 数据源元信息
    输出：选哪些数据源 + SQL/筛选条件 + 图表类型
    """
    prompt = f"""你是数据查询规划器。根据用户问题，选择合适的数据源并生成精准查询方案。

可用数据源：
{ds_metadata}

用户问题："{question}"

返回 JSON：
{{
  "queries": [
    {{
      "dsId": "数据源ID",
      "dsName": "数据源名称",
      "description": "查询目的（10字内）",
      "sql": "SELECT语句（见规则）",
      "apiFilter": null
    }}
  ],
  "chartType": "line|bar|pie|table|kpi|gauge|radar|none",
  "chartTitle": "图表标题"
}}

【SQL 生成规则（严格遵守）】
- database 类型必须生成 SQL
- 必须加 WHERE 条件（如问题涉及筛选）
- 必须加 GROUP BY + 聚合函数（如问题问总量/均值/对比）
- 必须加 ORDER BY（如问题问排名/最高/最低）
- 【强制】必须加 LIMIT，最大值 200（例：LIMIT 50, LIMIT 200）
- 不能 SELECT *（除非必要），应只选所需字段
- 只允许 SELECT，不能有 INSERT/UPDATE/DELETE/DROP
- api 类型：sql 留空，如需过滤填 apiFilter（如 {{"field":"category","value":"手机"}}）
- 可选多个数据源
- 简洁，不要废话"""

    return await chat_completion_json([
        {"role": "system", "content": "你是SQL查询生成器，只返回紧凑JSON，不要多余文字。"},
        {"role": "user", "content": prompt}
    ])


async def fetch_api_data(ds: dict) -> list:
    """获取 API 类型数据源的数据"""
    url = ds.get("url", "")
    if not url:
        return []
    if url.startswith('/'):
        url = f"http://127.0.0.1:8000{url}"
    try:
        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
            resp = await client.request(
                ds.get("method", "GET"), url,
                headers=ds.get("headers") or {}
            )
            if resp.status_code != 200:
                return []
            raw = resp.json()
            data = raw
            if ds.get("dataPath"):
                for part in ds["dataPath"].split('.'):
                    if isinstance(data, dict):
                        data = data.get(part, data)
            return data if isinstance(data, list) else [data]
    except Exception as e:
        print(f"[智能问数] API 获取失败 ({url}): {e}")
        return []


def apply_api_filter(rows: list, api_filter) -> list:
    """对 API 数据做简单过滤"""
    if not api_filter or not rows:
        return rows
    if isinstance(api_filter, dict):
        field = api_filter.get("field")
        value = api_filter.get("value")
        if field and value is not None:
            return [r for r in rows if str(r.get(field, "")) == str(value)]
    if isinstance(api_filter, list):
        result = rows
        for f in api_filter:
            result = apply_api_filter(result, f)
        return result
    return rows


# 安全查询行数上限：给 AI 分析用的数据最多 200 行，展示给用户的最多 50 行
_QUERY_HARD_LIMIT = 200
_DISPLAY_LIMIT = 50


def _enforce_sql_limit(sql: str, limit: int = _QUERY_HARD_LIMIT) -> str:
    """
    强制 SQL 带 LIMIT，防止全量扫描。
    
    - 已有 LIMIT: 取 min(原始值, hard_limit)
    - 没有 LIMIT: 将原始 SQL 包装为子查询并加 LIMIT
    - 只允许 SELECT，其他语句直接拒绝
    """
    sql = sql.strip().rstrip(';')
    sql_upper = sql.upper().lstrip()

    # 安全检查：只允许 SELECT
    if not sql_upper.startswith('SELECT'):
        raise ValueError(f"不允许执行非 SELECT 语句: {sql[:50]}")

    import re
    # 检查是否已有 LIMIT 子句
    limit_match = re.search(r'\bLIMIT\s+(\d+)', sql, re.IGNORECASE)
    if limit_match:
        existing = int(limit_match.group(1))
        # 如果已有 LIMIT 但超过上限，强制替换
        if existing > limit:
            safe_sql = re.sub(
                r'\bLIMIT\s+\d+', f'LIMIT {limit}', sql, flags=re.IGNORECASE
            )
            print(f"[智能问数] SQL LIMIT 过大 ({existing}→{limit})")
            return safe_sql
        return sql
    else:
        # 没有 LIMIT，包装为子查询
        # 对于聚合查询（含 GROUP BY）通常结果行数有限，但仍然加保护
        safe = f"SELECT * FROM ({sql}) AS _q LIMIT {limit}"
        print(f"[智能问数] SQL 无 LIMIT，自动加上: LIMIT {limit}")
        return safe


async def execute_query(ds: dict, query: dict) -> tuple:
    """执行单个查询，返回 (rows, fields)，强制行数安全上限"""
    ds_type = ds.get("type", "api")
    try:
        if ds_type == "database":
            from app.services.db_connector import query_sql
            raw_sql = query.get("sql") or f"SELECT * FROM {ds.get('table','?')}"
            # 强制加 LIMIT，防止全量扫描
            safe = _enforce_sql_limit(raw_sql, _QUERY_HARD_LIMIT)
            print(f"[智能问数] 执行SQL: {safe}")
            result = query_sql(safe)
            return result.get("data", []), result.get("fields", [])
        else:
            # API 类型：拉全量数据（API 本身限制），后端截断 + 过滤
            rows = await fetch_api_data(ds)
            # 先截断到上限，再过滤（避免 filter 前内存爆炸）
            rows = rows[:_QUERY_HARD_LIMIT]
            api_filter = query.get("apiFilter")
            if api_filter:
                rows = apply_api_filter(rows, api_filter)
            fields = list(rows[0].keys()) if rows else []
            return rows, fields
    except Exception as e:
        print(f"[智能问数] 查询失败 ({ds.get('name')}): {e}")
        return [], []


def extract_json_block(text: str) -> dict:
    """从 AI 输出中提取 ---JSON--- 标记后的 JSON 块"""
    marker = "---JSON---"
    idx = text.find(marker)
    if idx < 0:
        # 尝试找末尾的 JSON 对象
        last_brace = text.rfind("{")
        if last_brace >= 0:
            try:
                return json.loads(text[last_brace:])
            except json.JSONDecodeError:
                pass
        return {}
    json_str = text[idx + len(marker):].strip()
    # 去除可能的 markdown 代码块包裹
    json_str = json_str.strip('`').strip()
    if json_str.startswith('json'):
        json_str = json_str[4:].strip()
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        start = json_str.find('{')
        end = json_str.rfind('}')
        if start >= 0 and end > start:
            try:
                return json.loads(json_str[start:end + 1])
            except json.JSONDecodeError:
                pass
    return {}


async def ask_stream_generator(request: AskRequest):
    """
    智能问数 SSE 流式生成器

    Phase 1: AI 生成查询方案 → 展示查询意图
    Phase 2: 执行查询 → 立即展示数据表格
    Phase 3: AI 流式分析 → 文字逐字打出 + 结构化结果
    """
    from app.services.kimi import chat_completion_stream

    q = request.question.strip()
    all_ds = request.allDataSources or []

    if not all_ds:
        yield sse_event("error", {"message": "当前项目没有可用的数据源，请先到数据源管理中添加。"})
        return

    # ===== Phase 1: AI 生成查询方案 =====
    yield sse_event("step", {"phase": "plan", "status": "loading", "detail": "正在理解问题..."})

    try:
        ds_meta = build_ds_metadata(all_ds)
        plan = await generate_query_plan(q, ds_meta)
        queries = plan.get("queries", [])
        chart_type = plan.get("chartType", "table")
        chart_title = plan.get("chartTitle", "数据分析")
        print(f"[智能问数] 查询方案: {len(queries)} 个查询, 图表: {chart_type}")
    except Exception as e:
        print(f"[智能问数] Phase1 失败: {e}")
        yield sse_event("error", {"message": f"查询规划失败: {str(e)}"})
        return

    yield sse_event("step", {"phase": "plan", "status": "done", "detail": f"已生成 {len(queries)} 个查询方案"})

    # 推送查询方案
    for query in queries:
        yield sse_event("query", {
            "dsId": query.get("dsId"),
            "dsName": query.get("dsName"),
            "sql": query.get("sql"),
            "description": query.get("description"),
        })

    if not queries:
        yield sse_event("error", {"message": "AI 未能生成有效的查询方案，请换一种方式提问。"})
        return

    # ===== Phase 2: 执行查询 =====
    yield sse_event("step", {"phase": "query", "status": "loading", "detail": "正在查询数据..."})

    # 找到对应的数据源配置
    ds_map = {ds.get("id"): ds for ds in all_ds}
    query_results = {}

    for query in queries:
        ds_id = query.get("dsId")
        ds = ds_map.get(ds_id)
        if not ds:
            # 尝试按名称匹配
            ds = next((d for d in all_ds if d.get("name") == query.get("dsName")), None)
        if not ds:
            print(f"[智能问数] 找不到数据源: {ds_id}")
            continue

        rows, fields = await execute_query(ds, query)
        query_results[ds_id or ds.get("id")] = {"rows": rows, "fields": fields, "dsName": ds.get("name")}

        # 每个查询完成立即推数据表格
        yield sse_event("table", {
            "dsId": ds.get("id"),
            "dsName": ds.get("name"),
            "columns": fields,
            "rows": rows[:50],
            "total": len(rows),
        })
        print(f"[智能问数] 查询完成: {ds.get('name')} → {len(rows)} 条")

    yield sse_event("step", {"phase": "query", "status": "done", "detail": f"已获取数据"})

    # ===== Phase 3: AI 流式分析 =====
    yield sse_event("step", {"phase": "analyze", "status": "loading", "detail": "正在分析数据..."})

    # 构建数据摘要给 AI
    data_parts = []
    all_rows_for_chart = []
    first_ds_id = None
    for ds_id, result in query_results.items():
        if not first_ds_id:
            first_ds_id = ds_id
        rows = result["rows"]
        fields = result["fields"]
        all_rows_for_chart = rows
        data_parts.append(f"【{result['dsName']}】共{len(rows)}条，字段: {', '.join(fields)}")
        # 给 AI 看前 30 行（查询结果通常已被 SQL 精简过）
        for row in rows[:30]:
            data_parts.append(json.dumps(row, ensure_ascii=False))
        if len(rows) > 30:
            data_parts.append(f"...（共 {len(rows)} 条，仅展示前 30 条）")

    # 收集 Phase1 的 SQL（用于 widgetConfig，一键入板后组件直接用）
    first_query_sql = ""
    for query in queries:
        if query.get("sql"):
            first_query_sql = query["sql"]
            break

    analysis_prompt = f"""基于以下真实查询结果，回答用户的问题。

查询结果：
{chr(10).join(data_parts)}

用户问题："{q}"

请按以下格式回复：
1. 先用自然语言回答（2-4段，可以用 **加粗** 强调关键数字，用 - 列表列举要点）
2. 分析完毕后，另起一行输出 ---JSON--- 标记
3. 在标记后输出一个 JSON 对象，包含：
{{
  "kpi": [{{
    "label": "指标名",
    "value": "数值（已格式化，如 128.5万）",
    "unit": "单位",
    "trend": "up/down/flat",
    "change": "+12.3%"
  }}],
  "chart": {{
    "chartType": "{chart_type}",
    "title": "{chart_title}",
    "echartsOption": {{}}
  }},
  "widgetConfig": {{
    "type": "{chart_type}",
    "props": {{"title": "{chart_title}"}},
    "dataSource": {{
      "sourceId": "{first_ds_id}",
      "mapping": {{}},
      "sql": "{first_query_sql}"
    }}
  }}
}}

echartsOption 要求：
- 必须包含真实数据（从查询结果中提取）
- 使用暗色主题友好的配色（如 #00d4ff, #7b61ff, #36d399, #f59e0b）
- 文字颜色用 #8892b0
- 分割线颜色用 rgba(255,255,255,0.08)
- kpi 如果数据中无法提取明确的趋势则可留空数组
- 如果不适合做图表，chart 和 widgetConfig 可为 null
- widgetConfig.dataSource.mapping 要正确填写（x/y 或 name/value），不要留空
- widgetConfig.dataSource.sql 是添加到看板后组件执行的查询（已填好，保持不变）"""

    try:
        buffer = ""
        json_marker = "---JSON---"
        marker_found = False
        # pending 用于暂存可能是 marker 开头的文字，防止 marker 分 token 到达时泄露
        pending = ""

        async for token in chat_completion_stream([
            {"role": "system", "content": "你是专业数据分析师，擅长从数据中发现洞察并给出可视化建议。回答简洁有力。"},
            {"role": "user", "content": analysis_prompt}
        ]):
            buffer += token
            if marker_found:
                continue  # marker 已找到，后续 token 都是 JSON 部分，不推送

            pending += token

            if json_marker in pending:
                # marker 完整出现，推送 marker 之前的文字
                before = pending[:pending.index(json_marker)]
                if before:
                    yield sse_event("text", {"delta": before})
                marker_found = True
                continue

            # 如果 pending 末尾可能是 marker 的前缀，暂不推送
            safe_len = len(pending) - len(json_marker) + 1
            if safe_len > 0:
                yield sse_event("text", {"delta": pending[:safe_len]})
                pending = pending[safe_len:]

        # 流结束，解析结构化 JSON
        structured = extract_json_block(buffer)
        if structured:
            yield sse_event("result", structured)

    except Exception as e:
        print(f"[智能问数] Phase3 分析失败: {e}")
        yield sse_event("text", {"delta": f"\n\n分析过程出现问题: {str(e)}"})

    yield sse_event("step", {"phase": "analyze", "status": "done", "detail": "分析完成"})
    yield sse_event("done", {})


@router.post("/ask")
async def ask_data(request: AskRequest):
    """
    智能问数 — SSE 流式端点

    Phase 1: AI 生成查询方案（JSON 模式）→ 展示查询意图
    Phase 2: 执行真实查询 → 立即展示数据表格
    Phase 3: AI 流式分析 → 文字逐字打出 + 图表/KPI
    """
    return StreamingResponse(
        ask_stream_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
