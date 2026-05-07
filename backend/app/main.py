"""
AI 看板平台 - FastAPI 后端入口
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ai, data, export, mock_data, projects
from app.config import settings

# 支持路径前缀（用于反向代理部署）
API_PREFIX = os.getenv("API_PREFIX", "/kanban")  # 默认使用 /kanban 前缀

app = FastAPI(
    title="AI 看板平台 API",
    description="AI-First 看板生产系统后端",
    version="0.1.0",
    root_path=API_PREFIX  # 设置根路径前缀
)

# CORS 配置（开发环境允许前端 dev server）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(ai.router, prefix="/api/ai", tags=["AI"])
app.include_router(data.router, prefix="/api/data", tags=["数据源"])
app.include_router(export.router, prefix="/api/export", tags=["导出"])
app.include_router(mock_data.router, prefix="/api/mock", tags=["模拟数据"])
app.include_router(projects.router, prefix="/api/projects", tags=["项目管理"])


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}
