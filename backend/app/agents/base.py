"""
Agent 基类 - 所有 Agent 的公共接口
"""
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Agent 基类"""

    name: str = ""
    description: str = ""

    @abstractmethod
    async def execute(self, message: str, context: dict) -> dict:
        """
        执行 Agent 逻辑

        Args:
            message: 用户消息
            context: 上下文 {widgets, dataSources, selectedId, ...}

        Returns:
            {"commands": [...], "message": "..."}
        """
        pass

    def build_context_summary(self, context: dict) -> str:
        """将前端上下文序列化为 prompt 文本（精简版，减少 token 消耗）"""
        parts = []

        # 当前组件列表 — 只传布局关键信息，不传 props 细节
        widgets = context.get("widgets", [])
        if widgets:
            parts.append(f"当前画布上有 {len(widgets)} 个组件:")
            # 超过 12 个只显示摘要
            show_widgets = widgets[:12]
            for w in show_widgets:
                pos = w.get("position", {})
                size = w.get("size", {})
                ds_info = ""
                ds = w.get("dataSource") or {}
                if ds.get("sourceId"):
                    ds_info = f" ds={ds['sourceId']}"
                title = (w.get("props") or {}).get("title", "")
                title_str = f' "{title}"' if title else ""
                parts.append(f"  - [{w.get('type')}] id={w.get('id')} pos=({pos.get('x',0)},{pos.get('y',0)}) size=({size.get('w',0)}x{size.get('h',0)}){ds_info}{title_str}")
            if len(widgets) > 12:
                parts.append(f"  ... 还有 {len(widgets) - 12} 个组件未列出")

        # 数据源 — 只传 id/name/fields
        data_sources = context.get("dataSources", [])
        if data_sources:
            parts.append(f"\n已有 {len(data_sources)} 个数据源:")
            for ds in data_sources:
                fields = ds.get("fields", [])
                parts.append(f"  - id={ds.get('id', '?')} name={ds.get('name', '?')}: 字段 {fields[:10]}")

        # 选中状态
        selected_id = context.get("selectedId")
        if selected_id:
            parts.append(f"\n选中组件 ID: {selected_id}")

        return "\n".join(parts) if parts else "画布为空。"
