"""
布局 Agent - 智能语义排版

与快速排版(compute_layout)的本质区别：
- 快速排版：纯算法，按 type 分类 → 固定分行排列（0 token，瞬时）
- AI 排版：读取组件标题 + 数据源绑定，理解业务语义，智能决策谁更重要放 C 位

AI 仅返回 MOVE_WIDGET 和 RESIZE_WIDGET 命令，不增删组件。
"""
from app.agents.base import BaseAgent
from app.services.kimi import chat_completion_json

# ── System Prompt：语义决策框架（不复刻算法规则） ──────────────────

LAYOUT_SYSTEM_PROMPT = """你是数据大屏排版专家。根据组件的业务含义和数据绑定情况来排版画布(1920×1080)。

== 你会收到的信息 ==
每个组件：id / type / title / hasData(是否绑定了真实数据源) / dataFields(字段映射)
可能还有用户的排版意图描述。

== 核心决策：谁更重要 ==
1. hasData=true 的组件 > hasData=false 的组件（有真实数据的优先放视觉核心区）
2. type=map(地图) 必须放画布正中央(x≈480,y≈115,w≈960,h≈700)，是大屏的视觉重心
3. title 含"总""核心""关键""重要""营收""销售额"的 KPI，比其他 KPI 更大(w≈350,h≈180)
4. 有数据的图表(line/bar/pie)放主视区(画布中上)，无数据的图表放边缘/底部

== 用户意图（如果有）==
用户可能说："突出销售额""左边放指标""紧凑排列""数据图表要大"等。
有意图时完全尊重用户。无意图时用上面的规则自行判断。

== 布局硬约束 ==
- 画布 1920×1080，边距 ≥ 40px，组件间距 ≥ 16px
- text(标题) 放顶部居中，宽 1840，高 55
- clock 放右上角(不占行)，marquee 放底部全宽(高 45)
- 所有组件必须在画布内：x+w ≤ 1920, y+h ≤ 1080
- KPI/number-flip/progress 高度 120~180，图表高度 250~400

== 有地图时的布局 ==
- 地图居中作为视觉核心
- 其他组件分列两侧(左列 420 宽，右列 420 宽)
- 有数据的组件优先分到离地图更近的位置

== 无地图时的布局 ==
你可以灵活选择：
- 指标卡横排居中，图表按重要性分行
- 有数据的图表尽量大、占好位置
- 无数据的装饰组件(border-box, clock)不要抢核心区

== 输出格式（紧凑JSON，不要多余空格换行）==
{"commands":[{"type":"BATCH","payload":{"commands":[
{"type":"MOVE_WIDGET","payload":{"id":"xxx","position":{"x":N,"y":N}}},
{"type":"RESIZE_WIDGET","payload":{"id":"xxx","size":{"w":N,"h":N}}}
]}}],"message":"一句话说明排版思路"}

禁止输出 ADD_WIDGET 或 DELETE_WIDGET。"""


class LayoutAgent(BaseAgent):
    name = "layout"
    description = "智能语义排版 — 根据业务含义和数据绑定决策布局"

    async def execute(self, message: str, context: dict) -> dict:
        widgets = context.get("widgets", [])

        if not widgets:
            return {
                "commands": [],
                "message": "画布上没有组件，无需排版。请先添加一些组件。"
            }

        # ── 构建语义丰富的组件描述（精简 token） ──
        lines = []
        for w in widgets:
            wid = w.get("id", "?")
            wtype = w.get("type", "?")
            title = w.get("title") or (w.get("props") or {}).get("title", "")
            # 兼容两种 context 格式：工具栏(hasData/dataFields) 和对话框(dataSource.sourceId)
            ds = w.get("dataSource") or {}
            has_data = w.get("hasData", bool(ds.get("sourceId")))
            data_fields = w.get("dataFields") or ds.get("mapping") or {}

            parts = [wid, wtype]
            if title:
                parts.append(f'"{title}"')
            parts.append("有数据" if has_data else "无数据")
            if data_fields:
                # 精简字段映射：x=month,y=revenue
                mapping_str = ",".join(f"{k}={v}" for k, v in data_fields.items() if v)
                if mapping_str:
                    parts.append(f"映射={mapping_str}")
            lines.append(" ".join(parts))

        # ── 数据源概览（帮 AI 理解业务背景） ──
        ds_lines = []
        data_sources = context.get("dataSources", [])
        if data_sources:
            for ds in data_sources[:5]:  # 最多 5 个，省 token
                name = ds.get("name", "?")
                fields = ds.get("fields", [])
                ds_lines.append(f"  {name}: {','.join(fields[:8])}")

        # ── 组装用户消息 ──
        user_parts = []
        # 如果用户说的不只是"排版"，附上原始意图
        if message.strip() not in ("排版", "布局", "排列", "整理"):
            user_parts.append(f"排版意图：{message}")
        user_parts.append(f"\n{len(widgets)}个组件:")
        user_parts.append("\n".join(lines))
        if ds_lines:
            user_parts.append(f"\n数据源:")
            user_parts.append("\n".join(ds_lines))

        user_msg = "\n".join(user_parts)

        messages = [
            {"role": "system", "content": LAYOUT_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]

        print(f"[LayoutAgent] 开始 AI 语义排版，{len(widgets)} 个组件")
        result = await chat_completion_json(messages)

        # 安全检查：过滤掉任何 ADD/DELETE 命令
        if "commands" in result:
            result["commands"] = self._filter_commands(result["commands"])

        if "commands" not in result:
            result = {"commands": [], "message": "排版失败，请重试"}

        if not isinstance(result.get("commands"), list):
            result["commands"] = []

        cmd_count = sum(
            len((c.get("payload") or {}).get("commands", []))
            if c.get("type") == "BATCH" else 1
            for c in result["commands"]
        )
        print(f"[LayoutAgent] AI 语义排版完成，返回 {cmd_count} 条子命令")
        return result

    def _filter_commands(self, commands):
        """安全过滤：只保留 MOVE_WIDGET、RESIZE_WIDGET 和包含它们的 BATCH"""
        safe = []
        for cmd in commands:
            if not isinstance(cmd, dict):
                continue
            cmd_type = cmd.get("type", "")
            if cmd_type in ("MOVE_WIDGET", "RESIZE_WIDGET"):
                safe.append(cmd)
            elif cmd_type == "BATCH":
                sub_cmds = (cmd.get("payload") or {}).get("commands", [])
                filtered_subs = self._filter_commands(sub_cmds)
                if filtered_subs:
                    safe.append({
                        "type": "BATCH",
                        "payload": {"commands": filtered_subs}
                    })
        return safe
