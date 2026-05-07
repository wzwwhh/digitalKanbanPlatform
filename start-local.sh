#!/bin/bash
# 本地开发环境启动脚本 (Linux/Mac)

echo "=== 启动本地开发环境 ==="

# 检查端口占用
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "警告: 端口 8000 已被占用"
fi

if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "警告: 端口 5173 已被占用"
fi

# 启动后端
echo -e "\n[1/2] 启动后端服务..."
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

sleep 2

# 启动前端
echo "[2/2] 启动前端服务..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo -e "\n✅ 服务启动完成!"
echo "前端: http://localhost:5173"
echo "后端: http://localhost:8000"
echo -e "\n后端 PID: $BACKEND_PID"
echo "前端 PID: $FRONTEND_PID"
echo -e "\n按 Ctrl+C 停止服务"

# 等待用户中断
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
