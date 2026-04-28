"""
AI 路由 - 三层意图路由 + Agent 调度

Level 1: 正则匹配（0 token）
Level 2: 关键词匹配（0 token）
Level 3: Agent 调用（Kimi token）

所有 AI 常量配置集中在 app/ai_config.py
"""
import re
from fastapi import APIRouter
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


# ========== 智能问数 ==========

class AskRequest(BaseModel):
    question: str
    dataSource: Optional[dict] = None
    allDataSources: Optional[list] = None
    projectId: Optional[str] = None


class AskResponse(BaseModel):
    answer: str = ""
    chartSuggestion: Optional[str] = None
    widgetConfig: Optional[dict] = None

# 关键词 → 图表类型映射（定义在 ai_config.py 中的 CHART_SUGGESTIONS）


@router.post("/ask", response_model=AskResponse)
async def ask_data(request: AskRequest):
    """智能问数 — 调用大模型，基于问题分析推荐图表并给出洞察"""
    from app.services.kimi import chat_completion_json
    q = request.question.strip()
    ds = request.dataSource
    all_ds = request.allDataSources

    # 构建上下文
    ds_context = ""
    if ds:
        fields = ds.get("fields") or []
        field_str = "、".join(fields) if fields else "未知"
        ds_name = ds.get("name", "未命名")
        ds_id = ds.get("id", "ds_unknown")
        ds_context = f"用户明确指定了数据源「{ds_name}」(ID: {ds_id})，该数据源包含以下可用的数据字段：{field_str}"
    elif all_ds:
        ds_list_str = ""
        for d in all_ds:
            fields = d.get("fields") or []
            field_str = "、".join(fields[:15])
            ds_list_str += f"- 数据源「{d.get('name')}」 (ID: {d.get('id')}) 包含字段: {field_str}\n"
        ds_context = f"用户未指定具体数据源。系统中有以下可用的数据源：\n{ds_list_str}\n你需要根据用户的问题，在上述数据源中挑选最合适的一个，并在回答中明确指出建议使用哪个数据源。"
    else:
        ds_context = "用户未选择具体数据源，且当前系统中无可用数据源。"

    prompt = f"""
当前状态：
{ds_context}

用户提问："{q}"

请你扮演一位资深的BI数据分析师，分析用户的问题。
1. 如果用户未指定数据源，请务必在回答开头明确指出你推荐使用哪个数据源来分析此问题，并解释原因。
2. 如果用户询问的是趋势、占比、对比等分析场景，请推荐最合适的图表类型标识（如 'line', 'bar', 'pie', 'table', 'number-flip' 等），不需要推荐时返回 null。
3. 你的回答（answer）需要非常专业：解释你为什么要生成这个图表，并总结数据分析的思路。
4. 【重要】为了实现“一键生成答案”，如果能匹配到数据源和图表，你必须返回一个 `widgetConfig` 对象，包含具体的图表配置。配置规范如下：
"widgetConfig": {{
    "type": "图表类型标识 (line/bar/pie/table/number-flip 等)",
    "props": {{ "title": "推荐的图表标题" }},
    "dataSource": {{
        "sourceId": "选中的数据源的 ID",
        "mapping": {{
            "x": "用作 X 轴/分类维度的字段名",
            "y": "用作 Y 轴/数值的字段名",
            "dimension": "饼图等用作分类的字段名",
            "measure": "数值字段名"
        }}
    }}
}}

请严格返回如下 JSON 格式：
{{
    "answer": "你给用户的专业详细指导（支持 Markdown 格式，语气专业且热情）",
    "chartSuggestion": "line 或 bar 或 pie 或 null",
    "widgetConfig": {{ ... }} // 可选，只有当推荐了图表且确定数据源映射时提供
}}
"""

    try:
        print(f"[智能问数] 开始调用大模型，问题：{q}")
        result = await chat_completion_json([
            {"role": "system", "content": "你是一个专业的数据看板分析助手。"},
            {"role": "user", "content": prompt}
        ])
        
        answer = result.get("answer", "抱歉，分析时出现了一些逻辑错误。")
        suggested = result.get("chartSuggestion")
        widget_config = result.get("widgetConfig")
        
        # 清洗图表类型
        valid_charts = ["line", "bar", "pie", "table", "number-flip", "progress", "radar", "scatter", "map", "kpi"]
        if suggested and suggested not in valid_charts:
            suggested = None
            
        print(f"[智能问数] 大模型回复完成。推荐图表: {suggested}")
        return AskResponse(
            answer=answer,
            chartSuggestion=suggested,
            widgetConfig=widget_config
        )
    except Exception as e:
        print(f"[智能问数] 大模型调用失败: {e}")
        return AskResponse(
            answer=f"抱歉，AI 大脑暂时走神了 ({str(e)})，请稍后再试。",
            chartSuggestion=None
        )
