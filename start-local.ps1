# 本地开发环境启动脚本 (Windows)

Write-Host "=== 启动本地开发环境 ===" -ForegroundColor Green

# 检查端口占用
$backendPort = netstat -ano | findstr ":8000"
$frontendPort = netstat -ano | findstr ":5173"

if ($backendPort) {
    Write-Host "警告: 端口 8000 已被占用" -ForegroundColor Yellow
}
if ($frontendPort) {
    Write-Host "警告: 端口 5173 已被占用" -ForegroundColor Yellow
}

# 启动后端
Write-Host "`n[1/2] 启动后端服务..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

Start-Sleep -Seconds 2

# 启动前端
Write-Host "[2/2] 启动前端服务..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "`n✅ 服务启动完成!" -ForegroundColor Green
Write-Host "前端: http://localhost:5173" -ForegroundColor White
Write-Host "后端: http://localhost:8000" -ForegroundColor White
Write-Host "`n按 Ctrl+C 停止服务" -ForegroundColor Yellow
