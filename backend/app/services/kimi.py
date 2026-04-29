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


async def chat_completion(messages: list, response_format: str = "json") -> str:
    """
    调用 Kimi 模型获取回复

    Args:
        messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
        response_format: "json" 要求返回 JSON 格式

    Returns:
        模型回复的文本内容
    """
    client = get_client()

    if not settings.MOONSHOT_API_KEY:
        raise RuntimeError("未配置 MOONSHOT_API_KEY，请在 backend/.env 中添加 MOONSHOT_API_KEY=你的Key")

    kwargs = {
        "model": settings.MOONSHOT_MODEL,
        "messages": messages,
        "temperature": settings.MOONSHOT_TEMPERATURE,
    }

    # Moonshot 支持 JSON 模式
    if response_format == "json":
        kwargs["response_format"] = {"type": "json_object"}

    try:
        print(f"[Kimi] 调用模型 {settings.MOONSHOT_MODEL}，temperature={settings.MOONSHOT_TEMPERATURE}")
        completion = await client.chat.completions.create(**kwargs)
        content = completion.choices[0].message.content
        print(f"[Kimi] 响应长度: {len(content)} 字符")
        return content
    except Exception as e:
        print(f"[Kimi] API 调用失败: {e}")
        raise RuntimeError(f"Kimi API 调用失败: {str(e)}")


async def chat_completion_json(messages: list) -> dict:
    """
    调用 Kimi 并解析 JSON 返回

    Returns:
        解析后的 dict
    """
    content = await chat_completion(messages, response_format="json")
    try:
        result = json.loads(content)
        print(f"[Kimi] JSON 解析成功")
        return result
    except json.JSONDecodeError as e:
        print(f"[Kimi] JSON 直接解析失败: {e}")

    # 尝试提取 markdown 代码块中的 JSON
    import re
    code_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
    if code_match:
        try:
            return json.loads(code_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 尝试提取裸 JSON 对象
    start = content.find('{')
    end = content.rfind('}')
    if start >= 0 and end > start:
        try:
            return json.loads(content[start:end + 1])
        except json.JSONDecodeError:
            pass

    # 尝试修复括号错误：LLM 偶尔将 {} 写成 ()
    fixed = content.replace('(', '{').replace(')', '}')
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # 尝试从修复后的内容提取 JSON 对象
    start = fixed.find('{')
    end = fixed.rfind('}')
    if start >= 0 and end > start:
        try:
            return json.loads(fixed[start:end + 1])
        except json.JSONDecodeError:
            pass

    print(f"[Kimi] 所有 JSON 解析尝试均失败，原始响应:\n{content}")
    raise ValueError(f"无法解析 JSON 响应 (前100字符): {content[:100]}")


async def chat_completion_stream(messages: list):
    """
    流式调用 Kimi 模型，逐 token yield

    用于智能问数等需要渐进显示的场景。
    """
    client = get_client()

    if not settings.MOONSHOT_API_KEY:
        raise RuntimeError("未配置 MOONSHOT_API_KEY")

    try:
        print(f"[Kimi] 流式调用 {settings.MOONSHOT_MODEL}")
        stream = await client.chat.completions.create(
            model=settings.MOONSHOT_MODEL,
            messages=messages,
            temperature=settings.MOONSHOT_TEMPERATURE,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content
    except Exception as e:
        print(f"[Kimi] 流式调用失败: {e}")
        raise RuntimeError(f"Kimi 流式调用失败: {str(e)}")
