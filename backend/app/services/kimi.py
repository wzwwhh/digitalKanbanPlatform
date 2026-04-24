"""
Kimi (Moonshot) API 封装
"""
import json
from openai import AsyncOpenAI
from app.config import settings


def get_client():
    """获取 Moonshot API 客户端"""
    return AsyncOpenAI(
        api_key=settings.MOONSHOT_API_KEY,
        base_url=settings.MOONSHOT_BASE_URL,
    )


async def chat_completion(messages: list, temperature: float = 0.7, response_format: str = "json") -> str:
    """
    调用 Kimi 模型获取回复

    Args:
        messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
        temperature: 创造性控制
        response_format: "json" 要求返回 JSON 格式

    Returns:
        模型回复的文本内容
    """
    client = get_client()

    kwargs = {
        "model": settings.MOONSHOT_MODEL,
        "messages": messages,
        "temperature": temperature,
    }

    # Moonshot 支持 JSON 模式
    if response_format == "json":
        kwargs["response_format"] = {"type": "json_object"}

    try:
        completion = await client.chat.completions.create(**kwargs)
        content = completion.choices[0].message.content
        return content
    except Exception as e:
        raise RuntimeError(f"Kimi API 调用失败: {str(e)}")


async def chat_completion_json(messages: list, temperature: float = 0.7) -> dict:
    """
    调用 Kimi 并解析 JSON 返回

    Returns:
        解析后的 dict
    """
    content = await chat_completion(messages, temperature, response_format="json")
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # 尝试提取 JSON 块
        start = content.find('{')
        end = content.rfind('}')
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        raise ValueError(f"无法解析 JSON: {content[:200]}")
