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
        """将前端上下文序列化为 prompt 文本"""
        parts = []

        # 当前组件列表
        widgets = context.get("widgets", [])
        if widgets:
            parts.append(f"当前画布上有 {len(widgets)} 个组件:")
            for w in widgets:
                props_str = ", ".join(f"{k}={v}" for k, v in (w.get("props") or {}).items())
                parts.append(f"  - [{w.get('type')}] id={w.get('id')} {props_str}")

        # 数据源
        data_sources = context.get("dataSources", [])
        if data_sources:
            parts.append(f"\n用户已有 {len(data_sources)} 个数据源:")
            for ds in data_sources:
                fields = ds.get("fields", [])
                parts.append(f"  - {ds.get('name', '未命名')}({ds.get('type')}): 字段 {fields}")

        # 选中状态
        selected_id = context.get("selectedId")
        if selected_id:
            parts.append(f"\n用户当前选中的组件 ID: {selected_id}")

        return "\n".join(parts) if parts else "画布为空，没有已有组件。"
