@echo off
setlocal

cd /d "%~dp0backend"
python -m uvicorn app.main:app --reload
