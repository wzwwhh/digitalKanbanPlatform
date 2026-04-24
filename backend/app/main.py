"""
AI 看板平台 - FastAPI 后端入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ai, data, export
from app.config import settings

app = FastAPI(
    title="AI 看板平台 API",
    description="AI-First 看板生产系统后端",
    version="0.1.0"
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


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}
