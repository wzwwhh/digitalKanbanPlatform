@echo off
echo ========================================
echo Starting AI Kanban Platform...
echo ========================================

echo.
echo [1/2] Starting Backend Service (FastAPI)...
start "Backend" cmd /k "cd backend && uvicorn app.main:app --reload"

echo [2/2] Starting Frontend Service (Vue 3 + Vite)...
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Startup commands sent! Please check the two new command prompt windows.
echo Frontend URL: http://localhost:5173
echo Backend URL: http://localhost:8000
echo ========================================
pause
