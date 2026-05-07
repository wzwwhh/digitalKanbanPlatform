#!/bin/bash
# 停止服务器服务

echo "=== 停止服务 ==="

# 停止后端
PIDS=$(pgrep -f "uvicorn app.main:app")
if [ -n "$PIDS" ]; then
    echo "停止后端服务 (PID: $PIDS)..."
    kill $PIDS
    sleep 1
    echo "✅ 后端已停止"
else
    echo "⚠️  后端未运行"
fi
