"""AI 意图匹配精度测试"""
import sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from app.routers.ai import try_keyword_match

tests = [
    # (消息, 上下文, 应该匹配?)
    ("换暗色主题", {}, True),
    ("所有卡片颜色改红色", {"widgets": [{"id": "w1"}, {"id": "w2"}]}, True),
    ("换成柱状图", {"widgets": [{"id": "w1", "type": "line", "props": {}}], "selectedId": "w1"}, True),
    ("撤销", {}, True),
    ("换森林绿主题", {}, True),
    # 不应该匹配的
    ("恢复数据", {}, False),
    ("这个图表好看", {"selectedId": "w1"}, False),
    ("帮我分析一下", {}, False),
    ("红色好看", {}, False),
    ("主题推荐一下", {}, False),
    ("改成什么风格好呢", {}, False),
]

async def run_tests():
    print("=" * 50)
    print("AI 意图匹配精度测试")
    print("=" * 50)
    passed = 0
    for msg, ctx, should_match in tests:
        result = await try_keyword_match(msg, ctx)
        matched = result is not None
        ok = matched == should_match
        passed += ok
        status = "✅" if ok else "❌"
        detail = result.get("message", "") if result else "→ LLM"
        print(f"  {status} [{msg}] {detail}")

    print(f"\n结果: {passed}/{len(tests)} 通过")

asyncio.run(run_tests())
