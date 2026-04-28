"""
API 探测服务 - 调用用户提供的 API 并分析返回结构
"""
import httpx
from typing import Optional


async def probe_api(url: str, method: str = "GET", headers: Optional[dict] = None) -> dict:
    """
    探测 API，返回字段列表和示例数据

    Returns:
        {
            "status": 200,
            "fields": ["field1", "field2"],
            "sample": [{...}],
            "structure": "object|array|..."
        }
    """
    # 处理相对路径（如 /api/mock/sales）→ 转为本地绝对路径
    if url.startswith('/'):
        url = f"http://127.0.0.1:8000{url}"

    try:
        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers)
            else:
                response = await client.request(method.upper(), url, headers=headers)

            status = response.status_code
            if status != 200:
                return {
                    "status": status,
                    "fields": [],
                    "sample": [],
                    "structure": f"HTTP {status}"
                }

            data = response.json()
            fields, sample, structure = analyze_json(data)

            return {
                "status": status,
                "fields": fields,
                "sample": sample,
                "structure": structure,
            }

    except httpx.TimeoutException:
        return {"status": -1, "fields": [], "sample": [], "structure": "请求超时"}
    except Exception as e:
        return {"status": -1, "fields": [], "sample": [], "structure": f"错误: {str(e)}"}


def analyze_json(data) -> tuple:
    """
    分析 JSON 数据结构，提取字段列表

    Returns:
        (fields, sample, structure_type)
    """
    if isinstance(data, list):
        # 数组：取第一个元素分析字段
        if len(data) > 0 and isinstance(data[0], dict):
            fields = list(data[0].keys())
            sample = data[:5]  # 取前 5 条
            return fields, sample, "array"
        return [], data[:5], "array"

    elif isinstance(data, dict):
        # 对象：可能是包装结构 {code, data, message}
        # 尝试找到实际数据数组
        for key in ["data", "result", "results", "items", "list", "records"]:
            if key in data and isinstance(data[key], list):
                inner = data[key]
                if len(inner) > 0 and isinstance(inner[0], dict):
                    fields = list(inner[0].keys())
                    return fields, inner[:5], f"object.{key}[]"
                return [], inner[:5], f"object.{key}[]"

        # 普通对象
        fields = list(data.keys())
        return fields, [data], "object"

    return [], [], type(data).__name__
