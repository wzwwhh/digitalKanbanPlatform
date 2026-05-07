#!/bin/bash
# 服务器部署启动脚本

set -e

echo "=== 数字看板平台 - 服务器部署 ==="

# 检查目录
if [ ! -d "backend" ] || [ ! -d "frontend/dist" ]; then
    echo "❌ 错误: 缺少必要的目录"
    echo "请确保在项目根目录执行此脚本"
    exit 1
fi

# 创建数据目录
mkdir -p data

# 安装后端依赖
echo -e "\n[1/3] 安装后端依赖..."
cd backend
pip install -r requirements.txt -q
cd ..

# 停止旧服务
echo "[2/3] 停止旧服务..."
pkill -f "uvicorn app.main:app" || true
sleep 1

# 启动后端服务
echo "[3/3] 启动后端服务..."
cd backend
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../data/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

sleep 2

# 检查服务状态
if curl -s http://localhost:8000/kanban/api/health > /dev/null 2>&1; then
    echo -e "\n✅ 部署成功!"
    echo "后端 PID: $BACKEND_PID"
    echo "后端日志: data/backend.log"
    echo "数据库: backend/projects.db"
    echo -e "\n请配置 nginx 并访问: http://your-server:5175/kanban/"
else
    echo -e "\n❌ 后端启动失败，请查看日志: data/backend.log"
    exit 1
fi
